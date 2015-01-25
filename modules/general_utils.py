def getSec(s):
    try:
        if len(s) == 2:
            s = s + ':00'
        l = s.split(':')
        return int(l[0]) * 60 + int(l[1])
    except ValueError:
        return 0