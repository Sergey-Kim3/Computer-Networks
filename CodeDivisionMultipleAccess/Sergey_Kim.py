def joiner(number):
    sequenceList = [[1, 1, 1, 1], # transposed list of orthogonal sequences
                [1, 1, -1, -1],
                [1, -1, 1, -1],
                [1, -1, -1, 1]]
    sequenceList2 = [[],[],[],[]] # list of orthogonal sequences, but not transposed
    sequenceList3 = [[],[],[],[]] # list containing total encoded sequence
    for i in range(1, number+1): # loop for transmitter bit input
        bit = int(input("Type which bit(1 or -1) you will give to transmitter " + str(i) + ": "))
        while bit != 1 and bit != -1: # validation for transmitter bit input (only -1 and 1 allowed)
            bit = int(input("Type the bit again: "))
        for num in range(4): # nested loop to fill sequenceList2 and 3 
            sequenceList2[i-1].append(sequenceList[num][i-1]) # copy unmodified sequences into sequenceList2 for Receivers
            sequenceList3[num].append(sequenceList[num][i-1] * bit) # output bit modified sequences into sequenceList3
    for i in range(4):
        sequenceList3[i] = sum(sequenceList3[i]) # transposed nature of sequenceList 3 allows us to find the total encoded sequence with one operation called sum
    print("Total encoded sequence: " + str(sequenceList3))
    
# decoding sequence
    for i in range (number):
        for j in range (4): # nested loop to multiply individual sequences with encoded total sequence
            sequenceList2[i][j] *= sequenceList3[j]
        sequenceList2[i] = sum(sequenceList2[i])/4 # divide the number by 4 bits
        print("Receiver " + str(i+1) + " decoded bit into: " + str(sequenceList2[i])) #output receiver decoded bits
    

# take input as number of transmitters/receivers:
number = int(input("Type how many transmitter/receiver pairs (2, 3 or 4) will participate: ")) #ask for transmitter/receiver number
while number != 2 and number != 3 and number != 4: # validation for transmitter/receiver number
    number = int(input("Type again out of 2, 3 or 4: "))
joiner(number) # start function
 