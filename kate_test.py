s = input()
d = ""
for x in list(s):
    if x not in d:
        d += x
print(d)