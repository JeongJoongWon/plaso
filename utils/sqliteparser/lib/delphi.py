
def ExtractFilePath(fn):
  p = fn.rfind('\\')
  if p == -1:
    p = fn.rfind('/')
    if p == -1: return ''
  return fn[0:p + 1]

def ExtractFileName(fn):
  p = fn.rfind('\\')
  if p == -1:
    p = fn.rfind('/')
    if p == -1: return fn
  return fn[p + 1:]

def ExtractFileExt(fn):
  p = fn.rfind('.')
  if p == -1: return ''
  return fn[p:]

def ChangeFileExt(fn, ext):
  p = fn.rfind('.')
  if p == -1: return ''
  return fn[:p] + ext

def FileExists(fn):
  try:
    f = open(fn, 'rb')
    f.close()
    return True
  except FileNotFoundError:
    return False

IncludeTrailingBackslash = lambda v: v + '\\' if v.find('/') == -1 else v + '/'
IncludeTrailingPathDelimiter = IncludeTrailingBackslash
