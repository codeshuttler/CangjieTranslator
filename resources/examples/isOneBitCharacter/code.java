boolean isOneBitCharacter(int[] bits) {
    int i;
    for (i = 0; i < bits.length - 1; i++) {
        i += bits[i];
    }
    return i == bits.length - 1;
}