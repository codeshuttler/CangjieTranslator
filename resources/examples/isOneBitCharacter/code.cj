func isOneBitCharacter(bits: Array<Int32>): Bool {
    var i = 0
    for (j in 0..bits.size - 1) {
        i += Int64(bits[j])
    }
    return i == bits.size - 1
}