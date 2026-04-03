(module
  (func (export "adjust") (param $score i32) (param $issues i32) (result i32)
    local.get $score
    local.get $issues
    i32.const 3
    i32.mul
    i32.add))
