import math


def solution(startHight, descentRate):
    lenHeight = len(startHight)
    ans = 0
    timePerCount = [0 for i in range(int(math.pow(10, 5)+1))]
    maxCount = -99999

    for i in range(lenHeight):
        a = startHight[i]
        b = descentRate[i]
        temp = round(a/b)
        timePerCount[temp] = timePerCount[temp]+1
        if temp > maxCount:
            maxCount = temp

    saveCount = 0

    for j in range(1, len(timePerCount)):
        saveCount = saveCount + 1

        if timePerCount[j] != 0:
            defeat = min(saveCount, timePerCount[j])
            ans = ans + defeat

            if saveCount < timePerCount[j] or maxCount < j:
                break

            saveCount = saveCount-defeat

    return ans


if __name__ == '__main__':
    startHeightT = [70, 50, 57, 91, 156, 133, 116, 70, 60, 144, 20, 9,
                    664, 22, 14, 72, 40, 117, 16, 46, 42, 30, 34, 44, 50,
                    2, 180, 100, 12, 32, 54, 40, 644, 160]

    descentRateT = [5, 2, 3, 7, 2, 7, 4, 2, 5, 6, 10, 3, 8, 2, 2, 6, 2,
                    3, 4, 2, 2, 2, 2, 2, 2, 2, 3, 4, 2, 4, 6, 2, 7, 10]

    print(solution(startHeightT, descentRateT))
