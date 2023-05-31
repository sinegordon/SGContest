sm = 0
mul = 1
for i in range(10):
    xs = input()
    x = float(xs)
    sm += x
    mul *= x
print(sm, mul)