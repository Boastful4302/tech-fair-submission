z=0
for x in range(4):
    for y in range(4):
        z+=2
print(z)

def dothis(x):
    return x+5

print(dothis(dothis(10)))