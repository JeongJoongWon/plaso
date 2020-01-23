import sys
from lib.delphi import *        # lib\delphi.py
from lib.yjSysUtils import *    # lib\yjSysUtils.py
from SQLiteCommon import *
from SQLiteCarving import *
import json


def __loadCarvingConfig(conf):
  """ Carving 설정 파일을 읽어들인다. """
  carvConfig = json.loads(conf)

  dbStruct = carvConfig[0]
  dbDump.textEncoding = TStrType(dbStruct['text_encoding'])  # 1 : utf-8

  tableStruct = carvConfig[1]
  tableColumns = tableStruct['columns']
  for i, (fieldName, fieldType) in enumerate(tableColumns.items()):
    fieldType = fieldType[0]
    v = None
    if fieldType == 'TEXT':        v = TTableColumnType.Str
    elif fieldType == 'INTEGER':   v = TTableColumnType.Int
    elif fieldType == 'DOUBLE':    v = TTableColumnType.Double
    elif fieldType == 'TIMESTAMP': v = TTableColumnType.TimeStamp 
    elif fieldType == 'FLOAT':     v = TTableColumnType.Float
    elif fieldType == 'VARCHAR':   v = TTableColumnType.Str
    elif fieldType == 'BLOB':      v = TTableColumnType.Blob
    elif fieldType == 'NVARCHAR':  v = TTableColumnType.Str
    elif fieldType == 'INT64':  v = TTableColumnType.Int
    else: 
      assert False, '(작업요) 확인 되지 않은 타입' 
    if v != None:
      tableColumns[fieldName][0] = v
  del v

  fields = list(tableColumns.keys())
  export_fields = tableStruct['export_fields']
  if not 'export_fields' in tableStruct:             # export_fields 설정이 없으면 모든 fields가 export대상이 된다.
    export_fields = list(tableColumns.keys())
    tableStruct['export_fields'] = export_fields
  lst = []
  for i in range(0, len(export_fields)):
    s = export_fields[i]
    if s[0] == '#': export_fields[i] = ''            # '#'이 들어간 필드문자는 뺀다. (임시로 사용안할 필드에 '#'을 붙인다)
    else: lst.append(fields.index(s))
  while len(export_fields) != len(lst): export_fields.remove('')
  tableStruct['export_fields_index'] = lst
  return carvConfig


def getDeletedRecords(conf, test_start = None, test_length = None):
  """ conf 설정 정보에 맞는 레코드 데이터를 Carving으로 구한다. """
  if type(conf) is str:  conf = __loadCarvingConfig(conf)
  if not (type(conf) is list): return None

  v = conf[0]['file']
  if (v != '') and (ExtractFilePath(v) == ''): 
    conf[0]['file'] = app_path + v
  srcFile = conf[0]['file']
  if ExtractFileExt(srcFile).lower() == '.db':   # .db 파일이면...
    dbDump.readSQLiteDbFile(srcFile)
    conf[0]['text_encoding'] = dbDump.textEncoding
  else:
    dbDump.loadFile(srcFile)
    if conf[0].get('text_encoding') == None: conf[0]['text_encoding'] = TStrType.stUTF8.value

  tableStruct = conf[1]
  tableName = tableStruct['table_name']
  tableColumns = tableStruct['columns']
  exportFields = tableStruct['export_fields']
  exportFieldsIndex = tableStruct['export_fields_index']
  fields = tuple(tableColumns.keys())
  SQLiteCarver = TSQLiteCarver(dbDump)
  dbDump.textEncoding = conf[0]['text_encoding']

  def pageFreeAreaProc(data, stPos, length, isFreeBlock = None, pageFlag = None):  # 콜백 함수
    if __debug__:
      p = '(pos : %d..%d)' % (stPos, stPos + length)
      if isFreeBlock == None: print(p)
      else:
        if isFreeBlock: print('freeBlock: %s' % p)
        else: print('unallocated: %s' % p)
    dataLen = len(data)
    i = stPos
    stop = stPos + length
    while True:
      if (dataLen - i) < len(tableColumns): break
      if i >= stop: break
      xRec = []
      recInfo = SQLiteCarver.getRecordInfo(i, tableColumns)
      if recInfo == None: i += 1
      else:
        (xRec, i) = SQLiteCarver.getRecordData(recInfo, exportFieldsIndex)
        if len(xRec) > 0:
          xRecords.append(xRec)
          if __debug__: print(i, ',', xRec)
      if __debug__:
        if i % 1000 == 0: print(i)

  
  # result 포맷 : {"<Tabel Name>": <xRecords 포맷>}
  # xReocrds 포맷 : [[<Export Field Name 1>, ..., <Export Field Name N>], [<Field Data 1>,<Field Data 2>, ..., <Field Data N>], ...]
  result = {}      
  xRecords = [exportFields]    
  if (test_start == None) and (test_length == None):
    dbDump.enumFreeArea(pageFreeAreaProc)  
  else:
    if test_start == None: test_start = 0
    if test_length == None: test_length = len(SQLiteCarver.dbDump.data)
    if test_start >= len(dbDump.data): return None
    if (test_start + test_length) > len(SQLiteCarver.dbDump.data): 
      test_length = len(SQLiteCarver.dbDump.data) - test_start
    pageFreeAreaProc(SQLiteCarver.dbDump.data, test_start, test_length)
  result[tableName] = xRecords  
  return result


def printHelp():
  print(
  """
지정 테이블의 삭제된 레코드를 보여줍니다.

  SQLiteCarver <json 설정 파일명>

<json 설정 파일명>은 SQLiteParser로 생성할 수 있습니다.
이 json 설정 파일에는 확인할 테이블에 대한 상세 정보가 json 포맷으로 등록되어 있습니다.

사용예>
  >SQLiteParser.py external.db files /make_carvconf_file          
  >SQLiteParser.py external.db files /view_fields:_data,date_added,date_modified,media_type /make_carvconf_file

  >python.py SQLiteCarver
  >python.py -O SQLiteCarver carvconf_external_files.json
  """)


#
# main()
#
argv = sys.argv
#argv = [__file__, 'carvconf_Photos_ZGENERICASSET.json']  
argc = len(argv)
if argv[0] == __file__:   
  # SQLiteCarver.py를 메인으로 실행한 경우만 여기에 진입한다. (다른 모듈이 메인인 경우는 진입하지 않음)
  app_path = IncludeTrailingBackslash(os.path.dirname( os.path.abspath( __file__ ) ))  # 현재 소스 경로

  """
    >SQLiteCarver.py <carvconf Filename>       ; Carving 설정 내용에 맞는 Records를 구한다.

    >python SQLiteCarver.py carvconf_external_files.json
    >python -O SQLiteCarver.py carvconf_external_files.json
  """
  if argc < 2:
    printHelp()
    exit()

  fileName = argv[1]
  if ExtractFilePath(fileName) == '': fileName = app_path + fileName
  if not FileExists(fileName):
    print('Error: File not found')
    exit()

  f = open(fileName, 'rt')
  conf = f.read()
  f.close()
  print(getDeletedRecords(conf))

