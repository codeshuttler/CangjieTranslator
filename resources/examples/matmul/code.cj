from std import collection.*
from std import math.*
from std import time.*
from std import os.process.*

func matgen(n: Int64, seed: Float64): Array<Array<Float64>> {
    var a = Array<Array<Float64>>(n, { _ => Array<Float64>(n, item: 0.0)})
    var tmp = Float64(seed / Float64(n * n))
    for (i in 0..n) {
        for (j in 0..n) {
            a[i][j] = tmp * (Float64(i) - Float64(j)) * (Float64(i) + Float64(j))
        }
    }
    a
}

func matmul(a: Array<Array<Float64>>, b: Array<Array<Float64>>): Array<Array<Float64>> {
    let m = a.size
    let n = a[0].size
    let p = b[0].size
    var x = Array<Array<Float64>>(m, { _ => Array<Float64>(p, item: 0.0)})
    var c = Array<Array<Float64>>(p, { _ => Array<Float64>(n, item: 0.0)})
    
    for (i in 0..n) {
        for (j in 0..p) {
            c[j][i] = b[i][j]
        }
    }
    
    for (i in 0..m) {
        for (j in 0..p) {
            var s = 0.0
            for (k in 0..n) {
                s += a[i][k] * c[j][k]
            }
            x[i][j] = s
        }
    }
    return x
}

func calc(n: Int64): Float64 {
    var size = (n / 2) * 2
    var a = matgen(size, 1.0)
    var b = matgen(size, 2.0)
    var x = matmul(a, b)
    return x[size / 2][size / 2]
}

main() {
    var n = 1000;

    var left = calc(101)
    var right = -18.67
    if (math.abs(left - right) > 0.1) {
        println("${left} != ${right}")
        Process.current.exit(1)
    }

    // println("Cangjie\t${sys.pid()}")
    var start_time = DateTime.now().toUnixTimeStamp().toMilliseconds()
    var results = calc(n)
    var time_diff = DateTime.now().toUnixTimeStamp().toMilliseconds() - start_time
    println("stop")

    println(results)
    println("time: ${Float64(time_diff) / 1000.0} s")
}
