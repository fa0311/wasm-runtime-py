(module
  (type (;0;) (func (param i32) (result i32)))
  (type (;1;) (func))
  (func (;0;) (type 0) (param i32) (result i32)
    local.get 0
    i32.const 1
    i32.le_s
    if (result i32)  ;; label = @1
      i32.const 1
    else
      local.get 0
      i32.const 1
      i32.sub
      call 0
      local.get 0
      i32.const 2
      i32.sub
      call 0
      i32.add
    end)
  (func (;1;) (type 1)
    i32.const 15
    i32.const 2
    i32.sub
    call 0
    drop)
  (export "_start" (func 1)))
