def ModelIt(fromUser  = 'Default', rating = 0):
  print 'The rating is %d' % rating
  result = rating/10.0
  if fromUser != 'Default':
    return result
  else:
    return 'check your input'
