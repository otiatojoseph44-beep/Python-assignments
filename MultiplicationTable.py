number=int(input("enter number"))

for i in range(number,0,-1):
    
    for j in range(number,0,-1):
        
        print(f"{i*j}\t",end=" ")
        
    print()
