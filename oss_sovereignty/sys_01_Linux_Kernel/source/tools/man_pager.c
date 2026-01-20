#include <stdint.h>
#include <stddef.h>
#define copy_nonoverlapping(src, dst, count) __builtin_memcpy(dst, src, (count) * sizeof(*(src)))

void main() {
Vec<String> args = std__env__args().collect();if args.len()>1{__auto_type c = std__fs__read_to_string(&args[1]).unwrap();println!("{}",c);}
}
