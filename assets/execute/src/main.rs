extern "C" {
    fn execute(a: *const u8, len: usize) -> i32;
}

fn main() {
    let a = "\x41\x01\x0b\x0b"; // i32.const 1
    let b = "\x41\x02\x0b\x0b"; // i32.const 2
    let c = "\x6a\x0b"; // i32.add

    let d = format!("{}{}{}", a, b, c);

    let result = unsafe { execute(d.as_ptr(), d.len()) };
    println!("Result: {}", result);
}