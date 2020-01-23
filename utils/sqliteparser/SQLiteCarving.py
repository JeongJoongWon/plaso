from lib.yjSysUtils import *
from SQLiteCommon import *

def isValidStr(s):
  for i in range(0, len(s)):
    v = ord(s[i])
    if (v in range(0, 0x1f + 1)) and (not v in [9, 10, 13]):
      return False
  return True

TRecordInfo = type('TRecordInfo', (), dict(tableColumns = {}, fieldDataTypeInfos = [], lengthOfRecord = 0, stPos_FieldDataTypes = 0, stPos_RecordData = 0))

"""
  TSQLiteCarver:
    .getRecordInfo(self, stPos_FieldDataTypes, tableColumns)
    .getRecordData(self, recordInfo)
"""
class TSQLiteCarver:
  def __init__(self, dbDump):
     self.dbDump = dbDump
     pass

  def __del__(self):
    pass

  def getTextEncoding(self):
    return self.dbDump.textEncoding

  # http://ysbulpe.egloos.com/2282868
  def _isValidRecordInfo(self, recordInfo):
    """  
      recordInfo가 가지고 있는 실데이터에 대한 Field data types이 해당 Table의 Field Types에 포함될 수 있는 값인지 확인한다.
      만약 Field data type이 Table의 Field Types에 포함될 수 없는 Type이면 잘못된 recordInfo라고 할 수 있다.
    """
    for i, (key, value) in enumerate(recordInfo.tableColumns.items()):
      # fieldType이 'INTEGER'라면, dataType은 TFieldDataType.dtInt (1..8 bytes), dtConst0, dtConst1 이 들어갈 수 있다.
      dataType = recordInfo.fieldDataTypeInfos[i][1]     # dataType = (4, TFieldDataType.dtInt)[i]
      fieldType = value[0]                               # fieldType = [TTableColumnType.Str, 255][0]
      if fieldType == TTableColumnType.Str:
        if not dataType in [TFieldDataType.dtStr, TFieldDataType.dtNULL]:
          return False
      elif fieldType == TTableColumnType.Int:
        if not dataType in [TFieldDataType.dtConst0, TFieldDataType.dtConst1, TFieldDataType.dtInt, TFieldDataType.dtNULL]: 
          return False
      elif fieldType == TTableColumnType.Blob:
        if not dataType in [TFieldDataType.dtBLOB, TFieldDataType.dtNULL]: 
          return False
      elif fieldType in [TTableColumnType.Double, TTableColumnType.Float]:
        if not dataType in [TFieldDataType.dtConst0, TFieldDataType.dtConst1, TFieldDataType.dtInt, TFieldDataType.dtFloat, TFieldDataType.dtNULL]: 
          return False
      elif fieldType == TTableColumnType.TimeStamp: 
        if not dataType in [TFieldDataType.dtStr, TFieldDataType.dtFloat, TFieldDataType.dtNULL]:
          return False
      else: assert False
    return True

  def getRecordInfo(self, stPos_FieldDataTypes, tableColumns):
    """ 
      지정 위치의 RecordInfo를 구한다. 
      지정 위치는 레코드 Field data types이 있는 위치다.

      RecordInfo는 tableColumns, 레코드 실데이터가 있는 시작 위치(stPos_RecordData)와 레코드 실데이터에 대한 Type정보(fieldDataTypeInfos)등을 가지고 있다.
    """
    def getSize_FieldDataTytes(stPos_FieldDataTypes, fieldCount):
      i = fieldCount
      size = 0
      dbDump.position = stPos_FieldDataTypes
      while i > 0:
        if (dbDump.read(1, 'B') & 0x80) != 0:   # String, Blob
          size += 1
          if (dbDump.read(1, 'B') & 0x80) != 0: return 0 
        size += 1
        i -= 1
      return size

    def getRecordDataSize(fieldDataTypeInfos):
      size = 0
      for i in range(0, len(fieldDataTypeInfos)):
        size += fieldDataTypeInfos[i][0]
      return size

    # getRecordInfo()
    dbDump = self.dbDump
    try:
      size_FieldDataTypes = getSize_FieldDataTytes(stPos_FieldDataTypes, len(tableColumns))
      if size_FieldDataTypes > 0:
        fieldDataTypesBlob = dbDump.read(size_FieldDataTypes, stPos = stPos_FieldDataTypes)

        recordInfo = createObject(TRecordInfo)
        recordInfo.fieldDataTypeInfos = getFieldDataTypes(fieldDataTypesBlob)
        if recordInfo.fieldDataTypeInfos == []:
          #if __debug__: print('Error: FieldDataTypes 영역이 아닙니다. #2', end='\r')
          return None
        if __debug__: assert len(recordInfo.fieldDataTypeInfos) == len(tableColumns)
        recordInfo.lengthOfRecord = getRecordDataSize(recordInfo.fieldDataTypeInfos);   # 레코드 크기 (SQLite 레코드는 크기가 가변이다)
        recordInfo.stPos_FieldDataTypes = stPos_FieldDataTypes
        recordInfo.stPos_RecordData = stPos_FieldDataTypes + size_FieldDataTypes
        recordInfo.tableColumns = tableColumns
        if self._isValidRecordInfo(recordInfo): return recordInfo
        else: return None    
      else:
        #if __debug__: print('Error: FieldDataTypes 영역이 아닙니다. #1', end='\r')
        return None
    except TypeError:   # dbDump.data 범위를 벗어난 경우...
      return None

  def __getRecordData(self, recordInfo):
    recordData = []
    if recordInfo != None:
      pos = recordInfo.stPos_RecordData
      i = 0
      for i, (_, fieldType) in enumerate(recordInfo.tableColumns.items()):
        (v, pos) = self.dbDump.getAFieldData(i, recordInfo.fieldDataTypeInfos, stPos_FieldData = pos)
        if recordInfo.fieldDataTypeInfos[i][1] == TFieldDataType.dtNULL:  # 값이 NULL인 경우... (NULL값은 모든 DataType에 다 들어갈 수 있음)
          if fieldType[0] == TTableColumnType.Str: v = ''
          else: v = None
        if fieldType[0] == TTableColumnType.Str:  # "TEXT"
          ep = len(fieldType) - 1  
          if ep != 0:
            if type(fieldType[1]) is int:         # [TTableColumnType.Str, 1, 255, "UNIQUE"]
              if ('NOT NULL' in fieldType) and (v == None): break
              if (len(fieldType) >= 3) and not (fieldType[1] <= len(v) <= fieldType[2]): break
            if not type(fieldType[ep]) is int:    # [TTableColumnType.Str, "UNIQUE", "NOT NULL"] , "_data": [TTableColumnType.Str, 1, 255, "NOT NULL", "UNIQUE"]
              if ('NOT NULL' in fieldType) and (v == ''): break
              if 'UNIQUE' in fieldType: pass
          if (v == None) or ((len(v) > 0) and (v.replace('\x00', '') == '')): break    # TextEncoding이 안되었거나, 문자열이 '\x00'로 채워진 경우 잘못된 문자열로 본다.
        else:
          if (len(fieldType) >= 3) and not (fieldType[1] <= v <= fieldType[2]): break
        recordData.append(v)
      if len(recordData) != len(recordInfo.tableColumns): recordData = []
    return recordData

  def getRecordData(self, recordInfo, exportFieldsIndex = None):
    """ recordInfo의 record 데이터를 구한다. """
    i = recordInfo.stPos_FieldDataTypes
    result = []
    recordData = self.__getRecordData(recordInfo)
    if recordInfo.lengthOfRecord > 0:
      if len(recordData) != 0:
        if exportFieldsIndex != None: result = exportRecordFields(recordData, exportFieldsIndex)
        else: result = recordData
        i = recordInfo.stPos_RecordData + recordInfo.lengthOfRecord
      else:
        i = recordInfo.stPos_FieldDataTypes + len(recordInfo.fieldDataTypeInfos)  
    else: 
      i = recordInfo.stPos_FieldDataTypes + len(recordInfo.fieldDataTypeInfos)  
    return (result, i)
