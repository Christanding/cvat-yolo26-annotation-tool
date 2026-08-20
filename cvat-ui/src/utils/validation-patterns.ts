// Copyright (C) 2021-2022 Intel Corporation
// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

const validationPatterns = {
    validatePasswordLength: {
        pattern: /^(?=.{8,256}$)/,
        message: '密码长度必须为 8至256 个字符',
    },

    passwordContainsNumericCharacters: {
        pattern: /(?=.*[0-9])/,
        message: '密码至少包含 1 个数字',
    },

    passwordContainsUpperCaseCharacter: {
        pattern: /(?=.*[A-Z])/,
        message: '密码至少包含 1 个大写字母',
    },

    passwordContainsLowerCaseCharacter: {
        pattern: /(?=.*[a-z])/,
        message: '密码至少包含 1 个小写字母',
    },

    validateUsernameLength: {
        pattern: /^.{5,150}$/u,
        message: '用户名长度必须为 5至150 个字符',
    },

    validateUsernameCharacters: {
        pattern: /^[\p{L}\p{N}_@.+-]+$/u,
        message: '用户名只能包含字母、数字和 @/./+/-/_',
    },

    /*
        \p{Pd} - dash connectors
        \p{Pc} - connector punctuations
        \p{Cf} - invisible formatting indicator
        \p{L} - any alphabetic character
        Useful links:
        https://stackoverflow.com/questions/4323386/multi-language-input-validation-with-utf-8-encoding
        https://stackoverflow.com/questions/280712/javascript-unicode-regexes
        https://stackoverflow.com/questions/6377407/how-to-validate-both-chinese-unicode-and-english-name
    */
    validateName: {

        pattern: /^(\p{L}|\p{Pd}|\p{Cf}|\p{Pc}|['\s]){2,}$/gu,
        message: '名称格式不正确',
    },

    validateAttributeName: {
        pattern: /\S+/,
        message: '名称不能为空',
    },

    validateLabelName: {
        pattern: /\S+/,
        message: '名称不能为空',
    },

    validateAttributeValue: {
        pattern: /\S+/,
        message: '属性值不能为空',
    },

    validateURL: {

        pattern: /^(https?:\/\/)[^\s$.?#].[^\s]*$/, // url, ip
        message: 'URL 格式不正确',
    },

    validateOrganizationSlug: {
        pattern: /^[a-zA-Z\d]+$/,
        message: '只允许拉丁字母和数字',
    },

    validatePhoneNumber: {
        pattern: /^[+]*[-\s0-9]*$/g,
        message: '电话号码格式不正确',
    },
};

export default validationPatterns;
