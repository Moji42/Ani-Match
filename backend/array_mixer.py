def merge_top_bottom(arr1, arr2):

    mid1 = len(arr1) // 2  # midpoint for first array
    mid2 = len(arr2) // 2  # midpoint for second array

    merged_arr = arr1[:mid1] + arr2[mid2:]
    return merged_arr


def main():
    arr1 = [1, 2, 3, 4, 5, 6,23,3,4,5,5,6]
    arr2 = [10, 20, 30, 40, 50, 60]

    
    print("First array:", arr1)
    print("Second array:", arr2)
    merged = merge_top_bottom(arr1, arr2)
    print("Merged array:", merged)


if __name__ == "__main__":
    main()
