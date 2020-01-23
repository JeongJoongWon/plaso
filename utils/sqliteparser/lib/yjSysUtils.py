import os.path
import struct    # https://blog.naver.com/kinsoo007/221136581936

def findCmdSwitchInArgList(argList, switch, ignoreCase = True):
  """ 
    Argument List에서 command switch를 찾는다. 
  
    optViewFields = '/view_fields:'
    optDeletedRecords = '/deleted_records'
    argv = 'SQLiteParser.py external.db files /view_fields:_data,date_modified,date_added /deleted_records'.split()
    v1 = findArgSwitchInList(argv, optViewFields)       # _data,date_modified,date_added
    v2 = findArgSwitchInList(argv, optDeletedRecords)   # True
  """
  argc = len(argList)
  for i in range(1, argc):
    if ignoreCase:
       argv = argList[i].lower()
       switch = switch.lower()
    else:
      argv = argList[i]
    if argv == switch: return True
    elif argv.startswith(switch):
      value = argv[len(switch):]
      if value == '': return True
      else: return value
    else: False

# https://stackoverflow.com/questions/1398022/looping-over-all-member-variables-of-a-class-in-python
def createObject(className):
  """ 객체를 생성한다. """
  obj = className()
  members = [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("__")]  # class내 멤버변수를 구한다.
  for m in members:
     d = {list: [], dict: {}, tuple: (), set: {}}
     v = d.get(type(getattr(obj, m)))
     if v != None: setattr(obj, m, v)
  return obj

# https://sarc.io/index.php/development/857-python-bin-oct-dec-hex
def conv(number, base):
  """
    숫자를 진수 문자열로 변환한다.

    v = 10
    conv(v, 2)
    conv(v, 8)
    conv(v, 16)
  """
  T = "0123456789ABCDEF"
  i, j = divmod(number,base)

  if i == 0: return T[j]
  else: return conv(i,base)+T[j]


_types = {'BYTE': 1, 'WORD': 2, 'WORD-be': 2, 'DWORD': 4, 'DWORD-be': 4}

def getStructuredData(data, stPos, structure):
  pos = stPos
  result = {}
  for i, (varName, varType) in enumerate(structure.items()):
    if type(varType) is tuple: size = varType[0]   # varType = (16, 'utf-8')
    elif type(varType) is int: size = varType      # varType = 16
    else: size = _types[varType]                   # varType = 'WORD'
    v = data[pos: pos + size]

    if type(varType) is tuple:                     # var가 String type인 경우...
      try:
        v = v.decode(varType[1]).replace('\x00', '')
      except:
        v = ''
    elif type(varType) is str:
      if varType == 'BYTE': v = struct.unpack('<B', v)[0]         # 1Byte , unsigned char
      elif varType == 'WORD': v = struct.unpack('<H', v)[0]       # 2Byte , unsigned short
      elif varType == 'DWORD': v = struct.unpack('<I', v)[0]      # 4Byte , unsigned int
      elif varType == 'WORD-be': v = struct.unpack('>H', v)[0]    
      elif varType == 'DWORD-be': v = struct.unpack('>I', v)[0]   
    result[varName] = v
    #if __debug__: print('%d , %s , %s' % (i, varName, v))
    pos += size
  result = type('record', (), result)   # 정적 클래스로 정의한다.
  return (result, pos)

def blobToVal(blob, fmt):
  """ 이진 데이터를 숫자로 변환한다 """
  return struct.unpack(fmt, blob)[0]


class TDataAccess:
  def __init__(self, blob = ''):
    self.position = 0
    self.data = blob

  def __del__(self):
    self.data = ''
    pass

  def loadFile(self, fileName):
    f = open(fileName, 'rb')
    self.data = f.read()
    f.close()
    return len(self.data)

  def read(self, length, fmt = '', stPos = -1):
    """
      이진데이터(blob)내 특정 위치(stPos)의 데이터를 읽는다.  
      v = read(data, 1, 'B', pos)
      v = read(data, 4, stPos = pos)
    """
    if stPos == -1: stPos = self.position
    self.position = stPos + length
    blob = self.data[stPos: self.position]
    if blob != b'':
      if fmt == '': v = blob
      else: v = struct.unpack(fmt, blob)[0]
      return v
    else:    # 위치가 data를 벗어난 경우...
      return None

  def tell():
    return self.position

