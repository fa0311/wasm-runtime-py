(module
  (type (;0;) (func (result i32)))
  (type (;1;) (func))
  (func (;0;) (type 0) (result i32)
    (local i32 i32)
    i32.const 1
    local.set 0
    i32.const 0
    local.set 1
    block  ;; label = @1
      loop  ;; label = @2
        local.get 0
        i32.const 100
        i32.gt_s
        br_if 1 (;@1;)
        local.get 1
        local.get 0
        i32.add
        local.set 1
        local.get 0
        i32.const 1
        i32.add
        local.set 0
        br 0 (;@2;)
      end
    end
    local.get 1)
  (func (;1;) (type 1)
    call 0
    drop)
  (export "_start" (func 1)))
