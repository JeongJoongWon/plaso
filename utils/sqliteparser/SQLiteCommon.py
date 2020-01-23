from enum import Enum
from lib.yjSysUtils import *

# http://www.sqlite.org/fileformat2.html

def getDataType(DataTypesBlob, stPos = 0):
  """ 
    일련된 dataTypes(blob)에서 레코드의 임의 필드 데이터에 대한 Type을 구한다.
    
    stPos : (DataTypesBlob에서) 임의 필드 데이터에 대한 Data type이 있는 위치

    리턴값
      dataType : 필드 데이터의 Data type
      size : Data type이 명시된 장소의 크기
  """
  blobLen = len(DataTypesBlob)
  pos = stPos
  size = 0

  longlong = ''
  v = DataTypesBlob[pos]
  pos += 1
  size += 1
  while v & 0x80:                          # String or Blob Type인 경우...
    if size >= blobLen: break
    longlong += conv(v, 2).zfill(8)[1:]    # 최상위 1비트를 뺀 나머지 이진값(문자열)
    v = DataTypesBlob[pos]
    pos += 1
    size += 1

  if size > 8: assert False
  longlong += conv(v, 2).zfill(8)[1:]
  
  dataType = int(longlong, 2)               # 이진값(문자열)을 숫자로 전환
  return (dataType, size)


TTableColumnType = Enum('TTableColumnType', 'None Int Double Str Float Blob TimeStamp')
TFieldDataType = Enum('TFieldDataType', 'dtNotUsed dtInt dtFloat dtBLOB dtStr dtConst0 dtConst1 dtNULL')

TFieldDataList = {
  # <Type>: (<Size>, <FieldDataType>)
  0: (0, TFieldDataType.dtNULL), 
  8: (0, TFieldDataType.dtConst0),     # Field크기는 0지만 상수값 0을 의미한다.
  9: (0, TFieldDataType.dtConst1),     # Field크기는 0지만 상수값 1을 의미한다.
  1: (1, TFieldDataType.dtInt), 
  2: (2, TFieldDataType.dtInt), 
  3: (3, TFieldDataType.dtInt), 
  4: (4, TFieldDataType.dtInt), 
  5: (6, TFieldDataType.dtInt), 
  6: (8, TFieldDataType.dtInt), 
  7: (8, TFieldDataType.dtFloat),      # or TIMESTAMP
  10: (0, TFieldDataType.dtNotUsed),   # Not used. Reserved for expansion.
  11: (0, TFieldDataType.dtNotUsed)    # Not used. Reserved for expansion.
}

def getFieldDataTypes(fieldDataTypesBlob):

  def getNextSerialDataType(dataTypes, stPos):
    i = stPos
    if i < len(dataTypes): 
      (v, size) = getDataType(dataTypes, i)
      if __debug__: assert size in [1, 2]
      i += size
      return (v, i)
    else: return (None, None)

  dataTypes = fieldDataTypesBlob
  fieldDataTypes = [] 
  nextPos = 0
  while True:
    (dataType, nextPos) = getNextSerialDataType(dataTypes, nextPos)
    if dataType == None: return fieldDataTypes

    fieldDataTypeInfo = TFieldDataList.get(dataType)
    if fieldDataTypeInfo == None:  # String or Blob type 이면
      assert dataType >= 12
      """
        필드 데이터 타입(DataType) 값이 12이상이면, 필드 데이터가 String Type임을 의미한다.

        여기서..
        DataType에 대한 필드 데이터 길이를 구하려면...

        (DataType >= 12)이고 짝수(even)이면, (DataType - 12) / 2 = <데이터 길이>
        (Datatype >= 13)이고 홀수(odd)이면, (DataType - 13) / 2 = <데이터 길이>

        (GetStrDataType() 참조)
      """
      fieldDataTypeInfo = []  # (<데이터 길이>, <데이터 타입)
      if (dataType >= 12) and ((dataType & 0x1) == 0): 
        fieldDataTypeInfo.append((dataType - 12) // 2)     # (<데이터 길이> * 2) + 12 = dataType
        fieldDataTypeInfo.append(TFieldDataType.dtBLOB)    # 이진 데이터 (Blob)
      elif (dataType >= 13) and ((dataType & 0x1) == 1): 
        fieldDataTypeInfo.append((dataType - 13) // 2)     # (<데이터 길이> * 2) + 13 = dataType
        fieldDataTypeInfo.append(TFieldDataType.dtStr)
      else: 
        if __debug__: assert False
      fieldDataTypeInfo = tuple(fieldDataTypeInfo)

    fieldDataTypes.append(fieldDataTypeInfo)


def exportRecordFields(record, exportFieldsIndex):
  """ record에서 지정 Fields만 꺼낸다. """
  rec = []
  for i in range(0, len(exportFieldsIndex)):
    rec.append(record[exportFieldsIndex[i]])
  return rec

# String Type
class TStrType(Enum):
  stUTF8 = 1
  stUTF16le = 2
  stUTF16be = 3

class const(Enum):
  ReservedExpasion = bytearray(20)
  SQliteSignature = 'SQLite format 3'

class TSQLiteDump(TDataAccess):
  def __init__(self):
     super().__init__('')
     self.textEncoding = TStrType.stUTF8.value
     self.sqliteHeader = None 
     self.sizeOfSqliteHeader = 0
     pass

  def __del__(self):
    pass
    
  def readSQLiteDbFile(self, fileName):
    """ SQLiteDb 파일을 읽는다. """
    """
      TSqliteHeader = packed record
        arrSignature                       : array [0..15] of AnsiChar;
        wPageSize                          : WORD;                        // 512~23768 사이의 값을 가진다. 또는 1이다. 1일 경우 페이지의 크기는 65536. Big-Endian
        ucWriteVer                         : Byte;                        // 1 : lagacy, 2: WAL
        ucReadVer                          : Byte;                        // 1 : lagacy, 2: WAL
        ucReserved                         : Byte;                        // 각 페이지의 마지막 공백 보통은 0이다.
        ucMaxPayloadFration                : Byte;                        // 반드시 64
        ucMinPayloadFration                : Byte;                        // 반드시 32
        ucLeafPayloadFration               : Byte;                        // 반드시 32
        dwFileChangeCount                  : DWORD;                       // Big-Endian
        dwInHeaderDatabaseSize             : DWORD;                       // Big-Endian
        dwPageNumberFirstFreelistTrunkPage : DWORD;                       // Big-Endian
        dwTotalNumberFreelistPages         : DWORD;                       // Big-Endian
        dwSchemaCookie                     : DWORD;                       // Big-Endian
        dwSchemaFormatNumber               : DWORD;                       // 1,2,3 또는 4 Big-Endian
        dwDefaultPageCacheSize             : DWORD;                       // Big-Endian
        dwPageNUmberOfLargestRootBTreePage : DWORD;                       // when in auto-vacuum or incremental-vacuum modes, or zero otherwise.   -> 이것이 0 라면 dwIncrementalVacuumMode 은 무조건 0 다.
        dwDatabaseTextEncoding             : DWORD;                       // A value of 1 means UTF-8. A value of 2 means UTF-16le. A value of 3 means UTF-16be.  Big-Endian
        dwUserVersion                      : DWORD;                       // read and set by the user_version pragma. Big-Endian
        dwIncrementalVacuumMode            : DWORD;                       // True(0이 아니면) or False(0이면);   //Big-Endian
        dwApplicatoinID                    : DWORD;                       // Big-Endian
        arrReservedExpasion                : array [0..19] of AnsiChar;   // 무조건 0
        dwVersionValidForNumber            : DWORD;                       // Big-Endian
        dwSqliteVersion                    : DWORD;
      end;
    """
    sqliteHeader = {
        'Signature': (16, 'utf-8'),  # 0..15
        'PageSize': 'WORD-be', 
        'WriteVer': 'BYTE', 
        'ReadVer': 'BYTE',
        'Reserved': 'BYTE',
        'MaxPayloadFration': 'BYTE',
        'MinPayloadFration': 'BYTE',
        'LeafPayloadFration': 'BYTE',
        'FileChangeCount': 'DWORD-be',
        'InHeaderDatabaseSize': 'DWORD-be',
        'PageNumberFirstFreelistTrunkPage': 'DWORD-be',
        'TotalNumberFreelistPages': 'DWORD-be',
        'SchemaCookie': 'DWORD-be',
        'SchemaFormatNumber': 'DWORD-be',
        'DefaultPageCacheSize': 'DWORD-be',
        'PageNUmberOfLargestRootBTreePage': 'DWORD-be',
        'DatabaseTextEncoding': 'DWORD-be',
        'UserVersion': 'DWORD-be',
        'IncrementalVacuumMode': 'DWORD-be',
        'ApplicatoinID': 'DWORD-be',
        'ReservedExpasion': 20,     # 0..19
        'VersionValidForNumber': 'DWORD-be',
        'SqliteVersion': 'DWORD-be'
    }

    self.loadFile(fileName)  

    pos = 0
    st = pos
    (sqliteHeader, pos) = getStructuredData(self.data, pos, sqliteHeader)  # sqliteHeader를 읽는다.
    sizeOfSqliteHeader = pos - st
    del st, pos

    if not ((sqliteHeader.Signature == const.SQliteSignature.value) and (sqliteHeader.PageSize >= 512) and (sqliteHeader.DatabaseTextEncoding >= 1) and 
        (sqliteHeader.DatabaseTextEncoding <= 3) and (sqliteHeader.WriteVer in (1, 2)) and (sqliteHeader.ReadVer in (1, 2)) and
        (sqliteHeader.MaxPayloadFration == 64) and (sqliteHeader.MinPayloadFration == 32) and (sqliteHeader.LeafPayloadFration == 32) and
        (sqliteHeader.SchemaFormatNumber in (1, 2, 3, 4)) and (sqliteHeader.ReservedExpasion == const.ReservedExpasion.value)):
      return 0

    self.sqliteHeader = sqliteHeader
    self.textEncoding = sqliteHeader.DatabaseTextEncoding
    self.sizeOfSqliteHeader = sizeOfSqliteHeader
    return sizeOfSqliteHeader
  
  def enumFreeArea(self, pageFreeAreaProc):
    """ 
      SQLiteDb 파일내 사용되지 않은 빈영역들을 구한다. 

      def pageFreeAreaProc(data, stPos, length, isFreeBlock = None, pageFlag = None):
        #
        # 여기에 빈 영역에 대한 처리 코드를 둔다.
        #
        data = data[stPos: stPos + length]
        if __debug__:
          p = '(pos : %d..%d)' % (stPos, stPos + length)
          if isFreeBlock == None: print(p)
          else:
            if isFreeBlock: print('freeBlock, %s' % p)
            else: print('unallocated, %s' % p)

      enumFreeArea(FreeAreaProc)
    """
    data = self.data
    pos = 0
    sqliteHeader = {
      'Signature': (16, 'utf-8'),  # 0..15
      'PageSize': 'WORD-be'
    }
    (sqliteHeader, pos) = getStructuredData(data, pos, sqliteHeader) 
    if sqliteHeader.Signature != const.SQliteSignature.value: return False

    pageSize = sqliteHeader.PageSize
    pos = 0
    pageStPos = 0
    while True:
      pageStPos += pageSize
      if pageStPos >= len(data): break
      leafPageHeader = {
        'PageFlag': 'BYTE',                         # 0x5 : Internal page, 0xD : Leaf page
        'OffsetFirstBlockOfFreeSpace': 'WORD-be',   # FreeSpace의 FirstBlock 위치 (현재 안사용하는 영역), 여기에 삭제 데이터의 잔상이 남아있을 수 있음
        'NumberOfRecord': 'WORD-be',
        'OffsetOfFirstRecord':  'WORD-be',          # Offset of the first bytes Of The record
        'FragmentedFreeByte': 'BYTE',               # NumOfFragmentedFreeByes
      }     
      pos = pageStPos
      (leafPageHeader, pos) = getStructuredData(data, pos, leafPageHeader)   
      if leafPageHeader.PageFlag != 0xD: continue  # LeafPage가 아니면...
      sizeOfLeafPageHeader = pos - pageStPos
      
      #
      # LeafPage
      #
      offsetOfFreeSpace = sizeOfLeafPageHeader + (leafPageHeader.NumberOfRecord * 2)     # Cell offset list을 건너띈다.
      # offsetOFFreeSpace ~ FirstBlockOfFreeSpace 사이의 freeSpaceLength를 구한다.
      # (record의 실데이터는 page의 끝에서 올라온다는 것을 상기하자)
      freeSpaceLength = leafPageHeader.OffsetOfFirstRecord - offsetOfFreeSpace

      # Free space
      pos = pageStPos + offsetOfFreeSpace
      if callable(pageFreeAreaProc): pageFreeAreaProc(data, pos, freeSpaceLength, isFreeBlock = False)

      offsetNextFreeBlock = leafPageHeader.OffsetFirstBlockOfFreeSpace
      while offsetNextFreeBlock != 0:
        freeBlockChain = {
          'OffsetOfNextFreeBlock': 'WORD-be',
          'FreeBlockSize': 'WORD-be'
        }
        pos = pageStPos + offsetNextFreeBlock
        (freeBlockChain, pos) = getStructuredData(data, pos, freeBlockChain)

        pos = pageStPos + offsetNextFreeBlock
        if callable(pageFreeAreaProc): pageFreeAreaProc(data, pos, freeBlockChain.FreeBlockSize, isFreeBlock = True)
        
        offsetNextFreeBlock = freeBlockChain.OffsetOfNextFreeBlock
    return True

  # fieldDataTypeInfos = getFieldDataTypes(fieldDataTypesBlob)
  # (v, pos) = getAFieldData(i, fieldDataTypeInfos, stPos_FieldData = pos)
  # (v, pos) = getAFieldData(i, fieldDataTypeInfos, stPos_RecordData = pos)
  def getAFieldData(self, fieldIndex, fieldDataTypeInfos, stPos_FieldData = -1, stPos_RecordData = -1):
    """ fieldIndex의 Field data를 구한다. """
    sz = 0
    pos = stPos_FieldData
    if stPos_RecordData != -1:            # RecordData의 시작 위치(stPos)가 넘겨지면 이를 기점으로 fieldIndex 데이터가 있는 위치로 이동해서 Field Data를 구한다.
      assert(stPos_RecordData >= 0)
      for i in range(0, len(fieldDataTypeInfos)):
        if fieldIndex == i: break
        sz += fieldDataTypeInfos[i][0]    # (4, TFieldDataType.dtInt)[0]
      pos = stPos_RecordData

    pos += sz
    fieldDataType = fieldDataTypeInfos[fieldIndex]
    dataSize = fieldDataType[0]
    dataType = fieldDataType[1]
    if dataType == TFieldDataType.dtBLOB:
      # 포맷 : BLOB:<데이터위치>,<데이터크기>,(<데이터1>,<데이터2>)"
      v = 'BLOB:%d,%d' % (pos, dataSize)
      if dataSize == 1: v += ',(%.2X)' % dbDump.data[pos]
      else: v += ',(%.2X,%.2X)' % (dbDump.data[pos], dbDump.data[pos + 1])
    elif dataType == TFieldDataType.dtStr:
      strType = TStrType(self.textEncoding)
      try:
        dbDump.position = pos
        if strType == TStrType.stUTF8:      v = dbDump.read(dataSize).decode('utf-8')      
        elif strType == TStrType.stUTF16le: v = dbDump.read(dataSize).decode('utf-16-le')
        elif strType == TStrType.stUTF16be: v = dbDump.read(dataSize).decode('utf-16-be')
        else: assert False
      except UnicodeDecodeError:
        v = None
    elif dataType == TFieldDataType.dtConst0:
      if __debug__: assert dataSize == 0
      v = 0
    elif dataType == TFieldDataType.dtConst1:
      if __debug__: assert dataSize == 0
      v = 1
    elif dataType == TFieldDataType.dtInt:
      h = b''
      fmt = 'B'
      if dataSize == 2:
        fmt = '>H'            # unsigned sHort
      elif dataSize == 3:
        h = b'\x00'
        fmt = '>I'            # unsigned Int
      elif dataSize == 4:
        fmt = '>I'
      elif dataSize == 6: 
        h = b'\x00\x00'
        fmt = '>Q'            # unsigned long long
      elif dataSize == 8:
        fmt = '>Q'
      else:
        if __debug__: assert dataSize == 1
      v = blobToVal(h + dbDump.read(dataSize, stPos = pos), fmt)     
    elif dataType == TFieldDataType.dtFloat:
      if __debug__: assert dataSize == 8
      fmt = '>d'             # double
      v = blobToVal(dbDump.data[pos:pos + dataSize], fmt)
    else:
      if __debug__: assert dataType == TFieldDataType.dtNULL
      v = ''
    pos += dataSize
    return (v, pos)


dbDump = TSQLiteDump()
