#/usr/bin/env python3
import sys
from enum import Enum
import re                      # 정규 표현식 모듈
from lib.delphi import *       # lib\delphi.py
from lib.yjSysUtils import *   # lib\yjSysUtils.py
from SQLiteCommon import *
from SQLiteCarver import getDeletedRecords
#from SQLiteCarver import _test_1
import json


#
# SQLite Parser
#
# http://forensicinsight.org/wp-content/uploads/2013/07/INSIGHT-SQLite-데이터베이스-구조.pdf
# http://barbra-coco.dyndns.org/sqlite/fileformat.html#glossary_Database_file
# http://www.cse.unsw.edu.au/~cs3311/archive/exam/12s1/sqlite/fileformat2.html

"""
  query = 
  CREATE TABLE android_metadata (locale TEXT)
  CREATE TABLE thumbnails (_id INTEGER PRIMARY KEY,_data TEXT,image_id INTEGER,kind INTEGER,width INTEGER,height INTEGER)
  CREATE TABLE "files" (_id INTEGER PRIMARY KEY AUTOINCREMENT,_data TEXT UNIQUE COLLATE NOCASE,_size INTEGER,format INTEGER,parent INTEGER,date_added INTEGER,date_modified INTEGER,mime_type TEXT,title TEXT,description TEXT,_display_name TEXT,picasa_id TEXT,orientation INTEGER,latitude DOUBLE,longitude DOUBLE,datetaken INTEGER,mini_thumb_magic INTEGER,bucket_id TEXT,bucket_display_name TEXT,isprivate INTEGER,title_key TEXT,artist_id INTEGER,album_id INTEGER,composer TEXT,track INTEGER,year INTEGER CHECK(year!=0),is_ringtone INTEGER,is_music INTEGER,is_alarm INTEGER,is_notification INTEGER,is_podcast INTEGER,album_artist TEXT,duration INTEGER,bookmark INTEGER,artist TEXT,album TEXT,resolution TEXT,tags TEXT,category TEXT,language TEXT,mini_thumb_data TEXT,name TEXT,media_type INTEGER,old_id INTEGER,storage_id INTEGER,is_drm INTEGER,width INTEGER, height INTEGER,is_sound INTEGER default 0, year_name TEXT default \'<unknown>\', genre_name TEXT default \'<unknown>\',recently_played INTEGER default 0, most_played INTEGER default 0, recently_added_remove_flag INTEGER default 0,is_favorite INTEGER default 0, resumePos INTEGER default 0, isPlayed INTEGER default 0,face_count INTEGER default -1, scan_pri INTEGER default 0, weather_ID INTEGER default 0,recordingtype INTEGER default 0, group_id INTEGER default 0, city_ID INTEGER default 0,spherical_mosaic INTEGER default 0, is_3D INTEGER default 0, label_id INTEGER default 0,is_memo INTEGER default 0, addr TEXT, langagecode TEXT, is_secretbox INTEGER default 0,sampling_rate INTEGER default 0, bit_depth INTEGER default 0)

  CREATE TABLE sqlite_sequence(name,seq)
  CREATE TABLE "audio_genres_map" (genre_id INTEGER NOT NULL,UNIQUE (audio_id,genre_id) ON CONFLICT IGNORE)
  CREATE TABLE [Employee] ([EmployeeId] INTEGER  NOT NULL,  [LastName] NVARCHAR(20)  NOT NULL, ..., CONSTRAINT [PK_Employee] PRIMARY KEY  ([EmployeeId]), FOREIGN KEY ([ReportsTo]) REFERENCES [Employee] ([EmployeeId]) ON DELETE NO ACTION ON UPDATE NO ACTION)
"""
def _parseQuery(query):
  """ Query를 분석해서 Table명과 필드 정보를 구한다. """

  def trim(tokens):   # tokens = ['CREATE TABLE', '[Logs]', '(', '[Stats] NVARCHAR NOT NULL', ',', '[CheckedDate] TIMESTAMP, ..., ')']
    tokens = [v for v in tokens if v not in [' ', '']]  # 빈문자열은 뺀다.
    if __debug__: assert (len(tokens) > 2) and (tokens[0] == 'CREATE TABLE')
    for i in range(1, len(tokens)):   # tokens = ['CREATE TABLE', 'thumbnails', '(', ..., ')']
      v = tokens[i].strip()
      if v in ['(', ')', ',']: continue
      v = re.split('(NOT NULL|PRIMARY KEY|FOREIGN KEY|ON CONFLICT| )', v)
      v = [x for x in v if x not in [' ', '', 'ON CONFLICT']]
      if __debug__: assert type(v) is list
      fname = v[0]
      if fname[0] == '"': v[0] = fname.strip().strip('"')
      elif fname[0] == '[':
        v[0] = fname.strip().strip('[').strip(']')
      tokens[i] = v
    return tokens   # tokens = ['CREATE TABLE', ['Logs'], '(', ['Stats', 'NVARCHAR', 'NOT NULL'], ',', ['CheckedDate', 'TIMESTAMP'], ..., ')']

  query = ' '.join(query.split())  # 중복된(2개 이상) 공백 문자 제거한다. , 'CREATE    TABLE...' ---> 'CREATE TABLE...'
  if not query.startswith('CREATE TABLE'): return None
  fields = []
  schema = {}
  tokens = re.split('(\(|\)|\,|CREATE TABLE)', query)   # '(', ')', ',', 'CREATE TABLE'을 분리자로 해서 나눈다. (단, 분리자를 버리진 않음)
  tokens = trim(tokens)
  schema['#query'] = query
  schema['#fields'] = {}
  pk = False
  comma = True
  next_ = False
  if '(' in tokens:
    parenthesis = 1
    p = tokens.index('(')
    schema['#table'] = tokens[p - 1][0]        # '(' 전에 Table명이 있다고 본다.
    for i in range(p + 1, len(tokens)):
      v = tokens[i]
      if v == ',': 
        comma = True
        next_ = False
        continue
      if next_: continue
      attr = None
      if type(v) is list:
        name = v[0]           
        if name == 'FOREIGN KEY':
          next_ = True
          continue
        if len(v) == 1: 
          if pk: 
            pk = False
            schema['#primary_key'] = name
          continue
        else:
          if __debug__: 
            if name[0] == '#': continue 
          if name == 'CONSTRAINT': 
            if 'PRIMARY KEY' in v:
              pk = True
              if v.index('PRIMARY KEY') == len(v) - 1: continue
              schema['#primary_key'] = name     # ['CONSTRAINT', 'sqlite_autoindex_Logs_1', 'PRIMARY KEY'] , ['('] , ['FileName'] , [')']
            else: 
              continue
          attr = [v[1]]                         # ['TEXT']
        if 'NOT NULL' in v: 
          if __debug__: assert attr != None     # Type 없이 'NOT NULL' 인 구문은 허용되지 않음
          attr.append('NOT NULL')               # ['TEXT', 'NOT NULL']
        if 'PRIMARY KEY' in v: 
          schema['#primary_key'] = name
        if comma and (parenthesis == 1):        # ..., track INTEGER, year INTEGER CHECK(year!=0), is_ringtone INTEGER, ...          
          schema['#fields'][name] = attr
        comma = False
      elif v == '(': parenthesis += 1
      elif v == ')':
        parenthesis -= 1
        if parenthesis == 0: break
  return schema

class TPageFlag(Enum):
  pfInternalPage = 0x5
  pfLeafPage = 0xD
  pfIndexLeafPage = 0xA
  pfIndexInternalPage = 0x2
  pfOverflowPage = 0x0     

TPageInfo = type('TPageInfo', (), dict(pageFlag = TPageFlag.pfInternalPage, cellInfoList = []))
TInternalCellInfo = type('TInternalCellInfo', (), dict(pageNumber = 0, unknown_varint = 0))      # Child page number | (Unknown)
TLeafCellInfo = type('TLeafCellInfo', (), dict(lengthOfRecord = 0, rowId = 0, dataHeaderLength = 0, dataType = 0, fields = []))

"""
  TSQLiteParser:
    .databaseInfo
    .reset()
    .getTableNames(self)
    .getTableInfo(self, tableShowName) 
    .getRecordsInTable(self, tableShowName)
"""
class TSQLiteParser:

  def __init__(self, dbDump):
     self.dbDump = dbDump
     self.reset()
     pass

  def __del__(self):
    pass

  def reset(self):
    self.sqliteHeader = self.dbDump.sqliteHeader
    self.sizeOfSqliteHeader = self.dbDump.sizeOfSqliteHeader
    self.databaseInfo = None
    self.databaseInfo = self._getDatabaseInfo()

  def getTableNames(self):
    """ Database내 Table 목록을 구한다. """
  
    def _chktbl():
      if (tableInfo['schema'] == None) or (len(tableInfo['schema']['#fields']) == 0): return False
      for i, (_, v) in enumerate(tableInfo['schema']['#fields'].items()):
        if v == None: return False
      return True
    
    tableNames = []
    for i in range(0, len(self.databaseInfo)):
      tableInfo = self.databaseInfo[i]
      # tableInfo keys = 'type', 'tableShowName', 'targetTable', 'rootPage', 'query', 'schema'
      # 'type': 'table', 'index', ...
      if (tableInfo['type'] == 'table') and _chktbl(): 
        tableNames.append(tableInfo['tableShowName'])
    return tableNames

  def getTableInfo(self, tableShowName):
    for i in range(0, len(self.databaseInfo)):
      tableInfo = self.databaseInfo[i]    # {type: '', tableShowName: '', targetTable: '', rootPage: 0, query: ''}
      if tableInfo['tableShowName'] == tableShowName:
        if __debug__: assert tableInfo['type'] == 'table'
        return tableInfo
    return {}

  def getTextEncoding(self):
    return self.dbDump.textEncoding

  """
    Cell Header = [Length of Record | Row ID]
    Data Header = [Length of Data Header | Size of Field 1 | Size of Field 2 | ... | Size of Field N]
    
    Leaf Cell = [Cell Header][Data Header][Data of Field 1]Data of Field 2 | ... | Data of Field N]
  """
  def _getLeafCellRecord(self, stPos_LeafCell):
    """ 레코드 데이터를 가져온다. """

    def getLeafCellHeader(stPos_LeafCell):
      pos = stPos_LeafCell
      leafCellInfo = createObject(TLeafCellInfo)
      (leafCellInfo.lengthOfRecord, size) = getDataType(self.dbDump.data, pos)  # 레코드 길이
      if leafCellInfo.lengthOfRecord <= 0: return None
      pos += size
      (leafCellInfo.rowId, size) = getDataType(self.dbDump.data, pos) 
      pos += size
      stPos_dataHeader = pos   # Data Header 시작 위치
      (leafCellInfo.dataHeaderLength, size) = getDataType(self.dbDump.data, pos)
      pos += size
      return (leafCellInfo, stPos_dataHeader, pos)

    pos = stPos_LeafCell
    """
      leafCellInfo.dataHeaderLength: Data Header 크기
      stPos_dataHeader : Data Header 시작 위치
      stPos_fieldDataTypes: Data Header내 나열된 레코드 필드들의 데이터 타입(Size of Field N)의 시작 위치
      length_fieldDataTypes : 나열된 레코드 필드들의 데이터 타입 전체 크기
      stPos_RecordData : 레코드 필드 데이터가 있는 시작 위치
    """
    (leafCellInfo, stPos_dataHeader, pos) = getLeafCellHeader(pos)
    if __debug__: assert (len(leafCellInfo.fields) == 0) and (leafCellInfo.dataHeaderLength > 0)
    stPos_fieldDataTypes = pos
    length_fieldDataTypes = leafCellInfo.dataHeaderLength - (stPos_fieldDataTypes - stPos_dataHeader)
    stPos_RecordData = stPos_fieldDataTypes + length_fieldDataTypes                                
    fieldDataTypeInfos = getFieldDataTypes(self.dbDump.read(length_fieldDataTypes, stPos = stPos_fieldDataTypes))
    del length_fieldDataTypes, stPos_fieldDataTypes
    if __debug__: assert(stPos_RecordData == self.dbDump.position)

    leafCellInfo.fields = []
    pos = stPos_RecordData
    for i in range(0, len(fieldDataTypeInfos)):
      (v, pos) = self.dbDump.getAFieldData(i, fieldDataTypeInfos, pos)
      leafCellInfo.fields.append(v)

    if __debug__: assert len(leafCellInfo.fields) == len(fieldDataTypeInfos)
    return leafCellInfo


  def _getPageInfo(self, pageNumber):
    """ 지정 Page내 Cells 정보를 구한다. """

    def getInternalCellInfo(stPos):
      pos = stPos
      internalCellInfo = createObject(TInternalCellInfo) 
      internalCellInfo.pageNumber = self.dbDump.read(4, '>I', stPos)
      internalCellInfo.unknown_varint = ord(self.dbDump.read(1))   # (Unknown)
      return internalCellInfo

    def readPageHeader(pageStPos):
      pos = pageStPos
      # Page Header size : 12 Byte : Internal page, 8 Byte : Leaf page
      btreePageHeader = {
        'PageFlag': 'BYTE',                           # 0x5 : Internal page, 0xD : Leaf page
        'OffsetFirstBlockOfFreeSpace': 'WORD-be',     # FreeSpace의 FirstBlock 위치
        'NumberOfRecord': 'WORD-be',
        'OffsetOfFirstRecord':  'WORD-be',            
        'FragmentedFreeByte': 'BYTE',
        'PageNumberOfRightMostChildPage': 'DWORD-be'  # 이 Pagenumber of right most child-page는 Internal page에만 존재한다. (PageFlag가 0x5면 Internal page임)
      }
      st = pos
      (btreePageHeader, pos) = getStructuredData(self.dbDump.data, pos, btreePageHeader)
      sizeOfPageHeader = pos - st
      if __debug__: assert sizeOfPageHeader == 12
      return btreePageHeader
     
    def getPageStPos(pageNumber):
      if pageNumber == 1: p = self.sizeOfSqliteHeader          # page 시작위치는 sqliteHeader 다음부터 시작된다. 
      else: p = (pageNumber - 1) * self.sqliteHeader.PageSize  # 1번째 page는 sqliteHeader를 포함한다.
      return p

    def getCellOffsetList(pageStPos):
      cellOffsetList = []
      v = TPageFlag(pageHeader.PageFlag)
      if v in (TPageFlag.pfInternalPage, TPageFlag.pfIndexInternalPage): sizeOfPageHeader = 12
      elif v in (TPageFlag.pfLeafPage, TPageFlag.pfIndexLeafPage): sizeOfPageHeader = 8
      else: assert False
      if __debug__: 
        if pageNumber == 1: 
          assert pageStPos == self.sizeOfSqliteHeader    # 1번째 Page에는 SqliteHeader가 있음
      pos = pageStPos + sizeOfPageHeader                 # cellOffset list의 시작 위치
      if pageNumber == 1: pageStPos = 0
      for i in range(0, pageHeader.NumberOfRecord):
        v = self.dbDump.read(2, '>H', pos)
        pos = self.dbDump.position
        cellOffsetList.append(v + pageStPos) 
      return cellOffsetList

    offset = getPageStPos(pageNumber)
    pageHeader = readPageHeader(offset)            
    cellOffsetList = getCellOffsetList(offset) 
    assert pageHeader.NumberOfRecord == len(cellOffsetList)

    """
      cellOffsetList : Page내 있는 cells의 위치 정보를 가진다.

      각 cell들의 내용은 pageFlag에 따라 달라진다.
      현재 작업 페이지가 LeafPage이면 cell에는 실제 레코드 데이터를 가진다.
    """
    pageInfo = createObject(TPageInfo)
    pageInfo.pageFlag = TPageFlag(pageHeader.PageFlag)                             # Page 유형
    v = pageInfo.pageFlag
    if v == TPageFlag.pfInternalPage: 
      for i in range(0, len(cellOffsetList)):
        pageInfo.cellInfoList.append(getInternalCellInfo(cellOffsetList[i]))       # cell에 연관된 pageNumber속성 등을 구한다.
      # Page number of right most child-page
      r = createObject(TInternalCellInfo)
      r.pageNumber = pageHeader.PageNumberOfRightMostChildPage                     # Page number of right most child-page는 Internal page에만 존재한다.
      r.unknown_varint = 0
      pageInfo.cellInfoList.append(r)                                            
    elif v == TPageFlag.pfLeafPage: 
      pageInfo.cellInfoList = []
      for i in range(0, len(cellOffsetList)):
        pageInfo.cellInfoList.append(self._getLeafCellRecord(cellOffsetList[i]))     # 실데이터를 가지는 Records속성 등을 구한다.
    # Index Page
    elif v == TPageFlag.pfIndexInternalPage:                                         
      pageInfo.cellInfoList = []
      for i in range(0, len(cellOffsetList)):
        pageInfo.cellInfoList.append(getInternalCellInfo(cellOffsetList[i]))
    elif v == TPageFlag.pfIndexLeafPage:                                             
      pageInfo.cellInfoList = []
      for i in range(0, len(cellOffsetList)):
        pageInfo.cellInfoList.append(self._getLeafCellRecord(cellOffsetList[i]))
    return pageInfo

  def getRecordsInTable(self, tableShowName):
    """ 지정 Table의 레코드 데이터를 구한다. """
    records = []
    lstTablePageData = []

    tableInfo = self.getTableInfo(tableShowName)
    rootPage = tableInfo['rootPage']   # root Page Number
    tableSchema = tableInfo['schema']
    primaryKeyPos = -1
    if tableSchema.get('#primary_key') != None: 
      primaryKeyPos = tuple(tableSchema['#fields'].keys()).index(tableSchema['#primary_key'])  
    pageInfo = self._getPageInfo(rootPage)       
    pageFlag = pageInfo.pageFlag             
    if pageFlag == TPageFlag.pfInternalPage:
      for i in range(0, len(pageInfo.cellInfoList)):
        pageNumber = pageInfo.cellInfoList[i].pageNumber
        lstTablePageData.append(self._getPageInfo(pageNumber))
    elif pageFlag == TPageFlag.pfLeafPage:
      lstTablePageData.append(pageInfo)

    check = True
    while check:
      lstTablePageData2 = []
      for i in range(0, len(lstTablePageData)):
        pageFlag = lstTablePageData[i].pageFlag
        if pageFlag == TPageFlag.pfInternalPage:
          for j in range(0 , len(lstTablePageData[i].cellInfoList)):
            pageNumber = lstTablePageData[i].cellInfoList[j].pageNumber
            lstTablePageData2.append(self._getPageInfo(pageNumber))
        elif pageFlag == TPageFlag.pfLeafPage:
          for j in range(0 , len(lstTablePageData[i].cellInfoList)):
              record = []
              for n in range(0, len(lstTablePageData[i].cellInfoList[j].fields)):  
                if n == primaryKeyPos: v = lstTablePageData[i].cellInfoList[j].rowId    
                else: v = lstTablePageData[i].cellInfoList[j].fields[n]  
                record.append(v)
              records.append(record)
              del record

      check = len(lstTablePageData2) > 0
      if check: tablePageDataList = lstTablePageData2
    return records

  def _getDatabaseInfo(self):
    """ Database내 Tables 정보를 구한다. """
    if self.databaseInfo != None: return self.databaseInfo

    pageInfo = self._getPageInfo(1)
    # 1번째 Page는 db table정보를 가진 LeafPage로 연결된다.
    tableQueryDataList = []
    if pageInfo.pageFlag == TPageFlag.pfInternalPage:
      for i in range(0, len(pageInfo.cellInfoList)):
        pageNumber = pageInfo.cellInfoList[i].pageNumber
        tableQueryDataList.append(self._getPageInfo(pageNumber))
    elif pageInfo.pageFlag == TPageFlag.pfLeafPage:
      tableQueryDataList.append(pageInfo)
    del pageInfo

    dbInfo = []
    for i in range(0, len(tableQueryDataList)):
      for j in range(0, len(tableQueryDataList[i].cellInfoList)):
        tableInfo = {}
        leafCellInfo = tableQueryDataList[i].cellInfoList[j]
        tableInfo['type'] = leafCellInfo.fields[0]           # Type : table, index, trigger, view 
        tableInfo['tableShowName'] = leafCellInfo.fields[1]  # Table 표시 이름
        tableInfo['targetTable'] = leafCellInfo.fields[2]    # 대상 Table 이름
        tableInfo['rootPage'] = leafCellInfo.fields[3]       # Root Page Number
        query = leafCellInfo.fields[4]                       # Query
        if not query in ['', None]:
          tableInfo['query'] = query                           
          tableInfo['schema'] = _parseQuery(query)
          dbInfo.append(tableInfo)
    return dbInfo



def printHelp():
  print(
    """
SQLite .db 파일을 옵션에 맞춰 분석해 결과를 보여줍니다. 모든 결과는 json 포맷으로 출력됩니다.

  SQLiteParser.py <SQLite .db File> [Table Name]
  SQLiteParser.py <SQLite .db File> <<Table Name> </field_list|/deleted_records|/make_carvconf_file>>
  SQLiteParser.py <SQLite .db File> <<Table Name> </view_fields:<Field name 1>,...,<Field name N>
  
  SQLiteCarver.py <CarvConf. File>

사용예> 
    기본적으로 디버그 내용을 포함해 출력됩니다. 디버그 내용이 출력하지 않으려면 python -O 옵션과 함께 실행하면 됩니다.

    >python SQLiteParser.py external.db                                 external.db 파일내 테이블 목록을 보여줍니다.
    >python SQLiteParser.py external.db imagexmp                        external.db 파일내 imagexmp 테이블의 레코드 데이터를 보여줍니다.
    >python -O SQLiteParser.py external.db imagexmp                     (디버그 내용 없이) external.db 파일내 imagexmp 테이블의 레코드 데이터를 보여줍니다.
    >python SQLiteParser.py external.db imagexmp /field_list            external.db 파일내 imagexmp 테이블의 필드들을 보여줍니다.
    >python SQLiteParser.py external.db imagexmp /deleted_records       external.db 파일내 imagexmp 테이블의 삭제된 레코드들이 있는지 확인해 보여줍니다. 

    external.db 파일내 imagexmp 테이블의 레코드에서 view_fields에 지정된 필드 데이터를 보여줍니다.

      >python SQLiteParser external.db imagexmp /view_fields:image_id,capture_software,projection_type
    
    >python SQLiteParser.py external.db imagexmp /make_carvconf_file    Carving을 위한 설정 파일(carvconf_.json)을 생성합니다. 
    >python SQLiteParser.py external.db imagexmp /view_fields:image_id,capture_software,projection_type /make_carvconf_file

    Carving 설정 파일은 /make_carvconf_file 옵션을 이용해 생성할 수 있습니다.
    이 설정 파일은 SQLiteCarver로 SQLiteParser ... /deleted_records 옵션의 결과 보다 더 정확한 결과를 보고 싶을때 활용할 수 있습니다.
    즉, 이 설정 파일은 SQLiteParser에서 /deleted_records 옵션과 관련된 SQLiteCarver 모듈에서 사용됩니다.
    이 Carving 설정 파일을 생성 후, 이 설정 파일내 Carving 대상 테이블내 필드 범위를 직접 사용자가 수정하여 정확한 삭제 레코드의 결과가 나오게 개선할 수 있습니다.

      >python SQLiteCarver.py carvconf_external_imagexmp.json           Carving 설정 파일에 맞는 삭제 레코드(deleted_records)를 구한다.

    Carving 설정 수정 예>
      "media_type": ["INTEGER", "NOT NULL"] 을 
      "media_type": ["INTEGER", 1, 10, "NOT NULL"] 과 같이 숫자 범위를 지정하면 
      media_type 필드는 값이 1 ~ 10 범위의 값만 허용된다는 의미로 media_type값이 이를 초과하면 잘못된 레코드 데이터로 인식하고 출력하지 않는다.
  """)

#
# Main()
#
def main(argv, argc):

  """
    >python SQLiteParser
    >python -O SQLiteParser
    >python -O SQLiteParser external.db files

    >SQLiteParser <Database Filename>                                                     ; Table 목록을 보여준다.
    >SQLiteParser <Database Filename> <Table name>                                        ; Table의 Record들을 보여준다.
    >SQLiteParser <Database Filename> <Table name> /field_list                            ; Table의 Field 목록을 보여준다.
    >SQLiteParser <Database Filename> <Table name> /view_fields:<field 1>,...,<field N>   ; Table 레코드의 지정 Field들만 보여준다. 

    ; /deleted_records : Table의 삭제한 Record들을 보여준다.
    >SQLiteParser <Database Filename> <Table name> /deleted_records                       
    >SQLiteParser <Database Filename> <Table name> /view_fields:<field 1>,...,<field N> /deleted_records

    ; /make_carvconf_file : 카빙 설정 파일(json)을 만든다. (carvconf_<db_name>_<table_name>.json)
    >SQLiteParser <Database Filename> <Table name> /make_carvconf_file          
    >SQLiteParser <Database Filename> <Table name> /view_fields:<field 1>,...,<field N> /make_carvconf_file
  """
  optDisplayFieldNames = '/field_list'
  optViewFields = '/view_fields:'
  optDeletedRecords = '/deleted_records'
  optMakeCarvConfFile = '/make_carvconf_file'

  if __debug__:
    #argv = 'SQLitParser.py external_new.db'
    #argv = 'SQLitParser.py external.db'
    #argv = 'SQLitParser.py external_new.db files'
    #argv = 'SQLitParser.py external_new.db files /field_list'
    #argv = 'SQLitParser.py external.db files /make_carvconf_file'
    #argv = 'SQLitParser.py external.db files /deleted_records'
    #argv = 'SQLitParser.py external_new.db files /deleted_records'
    #argv = 'SQLiteParser.py external_new.db files /view_fields:_data,date_modified,date_added /deleted_records'
    #argv = 'SQLiteParser.py external_new.db files /view_fields:_data,ddd /deleted_records'
    #argv = 'SQLitParser.py test.db'
    #argv = 'SQLitParser.py test.db Logs'
    #argv = 'SQLitParser.py test.db Logs /deleted_records'
    #argv = 'SQLitParser.py test.db Logs /make_carvconf_file'
    #argv = 'SQLitParser.py'
    #argv = 'SQLiteParser.py Photos.sqlite ZGENERICASSET /view_fields:ZFILENAME'
    #argv = argv.split()
    pass


  argc = len(argv)
  if argc <= 1:
    printHelp()
    exit()

  if argc >= 2: 
    dbFileName = argv[1]
    if (dbFileName != '') and (ExtractFilePath(dbFileName) == ''): dbFileName = app_path + dbFileName
    if not FileExists(dbFileName):
      print('Error: File not found')
      exit()
    optDisplayTableNames = argc == 2
  if argc >= 3: tableName = argv[2]
  optViewFields = findCmdSwitchInArgList(argv, optViewFields, False)
  if optViewFields == None: optViewFields = []
  else: optViewFields = optViewFields.split(',')
  assert type(argv) is list
  optDeletedRecords = findCmdSwitchInArgList(argv, optDeletedRecords)
  optDisplayFieldNames = findCmdSwitchInArgList(argv, optDisplayFieldNames)
  optMakeCarvConfFile = findCmdSwitchInArgList(argv, optMakeCarvConfFile)

  # db 파일을 읽는다.
  if dbDump.readSQLiteDbFile(dbFileName) == 0:
    print('Error : This is not SQLite file.')
    exit()
  if __debug__: 
    print('DB File :', dbFileName, 'Size :', len(dbDump.data))

  sqliteParser = TSQLiteParser(dbDump)        # sqliteParser 객체 생성

  if optDisplayTableNames:                    # Tables 목록을 구한다.
    tableNames = sqliteParser.getTableNames()   
    print(tableNames)
    if __debug__: print('Count :', len(tableNames))
    exit()

  assert(tableName != '')
  tableInfo = sqliteParser.getTableInfo(tableName) 
  assert (tableInfo['targetTable'] == tableName) and (tableInfo['type'] == 'table') and (tableInfo['tableShowName'] == tableName)
  tableSchema = tableInfo['schema']
  fieldNames = tuple(tableSchema['#fields'].keys())
  if optDisplayFieldNames:                    # 지정 Table의 Fields 목록을 구한다.
    print(fieldNames)
    if __debug__: print('Count :', len(fieldNames))
    exit()

  # 확인할(출력할) 필드(ViewFields) 설정
  if len(optViewFields) == 0: exportFields = fieldNames
  else: exportFields = tuple(set(optViewFields) & set(fieldNames))  # 조사필드(ViewFields)에서 fieldNames에 없는 건 걸러낸다.

  if optMakeCarvConfFile or optDeletedRecords:
    # carving 처리를 위한 설정을 만든다.
    conf = [{'file': None, 'text_encoding': None}, {'table_name': None, 'primary_key': None, 'columns': None, 'export_fields': None}]
    columns = {}
    for i, (key, elem) in enumerate(tableSchema['#fields'].items()):
      columns[key] = elem     # {'_data': 'INTEGER', ...} ---> {'_data': ['INTEGER'], ...}
    conf[0]['file'] = dbFileName
    conf[0]['text_encoding'] = sqliteParser.getTextEncoding()
    conf[1]['table_name'] = tableName
    conf[1]['primary_key'] = tableSchema.get('#primary_key')
    conf[1]['columns'] = columns
    conf[1]['export_fields'] = exportFields
    del columns

    if optMakeCarvConfFile:
      fn = conf[0]['file']
      if __debug__: assert FileExists(fn)
      fn = app_path + 'carvconf_%s_%s.json' % (ChangeFileExt(ExtractFileName(fn), ''), tableName)
      f = open(fn, 'w')
      f.write(json.dumps(conf, indent = 3))   # conf를 JSON 문자열로 변환(=JSON Encoding) 후 인자로 넘긴다.
      f.close()
    else:
      if __debug__: assert optDeletedRecords
      r = getDeletedRecords(json.dumps(conf))
      #r = getDeletedRecords(json.dumps(conf), 3016, len(dbDump.data))   # TEST...
      print(r)
    exit()

  if __debug__: 
    assert(tableName == tableInfo['tableShowName'])
  records = sqliteParser.getRecordsInTable(tableName)   # 전체 레코드 데이터를 구한다.

  fields = fieldNames
  exportFieldsIndex = []
  for i in range(0, len(exportFields)):
    exportFieldsIndex.append(fields.index(exportFields[i]))

  # 출력 형식 = {"<Tabel Name>": [[<Export Field Name 1>, ..., <Export Field Name N>], [<Field Data 1>,<Field Data 2>, ..., <Field Data N>], ...]}
  line = '{"%s": [%s' % (tableName, exportFields) 
  if len(records) != 0: line += ', '
  print(line)
  last = len(records) - 1
  for i in range(0, len(records)):
    xRecordData = []
    record = records[i]
    xRecordData = exportRecordFields(records[i], exportFieldsIndex)
    line = '%s' % xRecordData
    if i != last: line += ', '
    print(line)
  print(']}')

  if __debug__:
    print('record count : ', len(records))


argv = sys.argv
argc = len(sys.argv)
if argv[0] == __file__:
  # SQLiteParser.py를 메인으로 실행한 경우만 여기에 진입한다. (다른 모듈이 메인인 경우는 진입하지 않음)
  app_path = IncludeTrailingBackslash(os.path.dirname( os.path.abspath( __file__ ) ))  # 현재 소스 경로
  main(argv, argc)
