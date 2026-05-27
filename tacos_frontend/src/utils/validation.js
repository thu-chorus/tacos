// 表单验证规则

// 学号验证
export function validateStudentId(rule, value, callback) {
  if (!value) {
    callback(new Error('请输入学号'))
  } else if (!/^\d{10}$/.test(value)) {
    callback(new Error('学号应为10位数字'))
  } else {
    callback()
  }
}

// 身份证验证
export function validateIdCard(rule, value, callback) {
  if (!value) {
    callback(new Error('请输入身份证号'))
  } else if (
    !/^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/.test(
      value
    )
  ) {
    callback(new Error('请输入正确的身份证号'))
  } else {
    callback()
  }
}

// 手机号验证
export function validatePhone(rule, value, callback) {
  if (!value) {
    callback(new Error('请输入手机号'))
  } else if (!/^1[3-9]\d{9}$/.test(value)) {
    callback(new Error('请输入正确的手机号'))
  } else {
    callback()
  }
}

// 邮箱验证
export function validateEmail(rule, value, callback) {
  if (!value) {
    callback(new Error('请输入邮箱'))
  } else if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(value)) {
    callback(new Error('请输入正确的邮箱格式'))
  } else {
    callback()
  }
}

// 密码验证
export function validatePassword(rule, value, callback) {
  if (!value) {
    callback(new Error('请输入密码'))
  } else if (value.length < 8) {
    callback(new Error('密码长度不能少于8位'))
  } else if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/.test(value)) {
    callback(new Error('密码必须包含大小写字母和数字'))
  } else {
    callback()
  }
}

// 车牌号验证
export function validateVehicleNumber(rule, value, callback) {
  if (!value) {
    callback() // 车牌号可以为空
  } else if (
    !/^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{4}[A-Z0-9挂学警港澳]$/.test(
      value
    )
  ) {
    callback(new Error('请输入正确的车牌号'))
  } else {
    callback()
  }
}

// 通用表单验证规则
export const commonRules = {
  required: {
    required: true,
    message: '此项为必填项',
    trigger: 'blur'
  },

  studentId: [
    { required: true, message: '请输入学号', trigger: 'blur' },
    { validator: validateStudentId, trigger: 'blur' }
  ],

  idCard: [
    { required: true, message: '请输入身份证号', trigger: 'blur' },
    { validator: validateIdCard, trigger: 'blur' }
  ],

  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { validator: validatePhone, trigger: 'blur' }
  ],

  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { validator: validateEmail, trigger: 'blur' }
  ],

  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { validator: validatePassword, trigger: 'blur' }
  ],

  vehicleNumber: [{ validator: validateVehicleNumber, trigger: 'blur' }]
}
