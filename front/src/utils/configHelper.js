/**
 * 配置数据转换工具
 * 原格式（Python/下划线命名）↔ 新格式（JavaScript/驼峰命名）
 */

/**
 * 下划线转驼峰
 * 例如：llm_provider → llmProvider
 */
function snakeToCamel(snakeStr) {
  if (!snakeStr || typeof snakeStr !== 'string') {
    return snakeStr
  }

  return snakeStr.replace(/_([a-z])/g, (match, letter) => {
    return letter.toUpperCase()
  })
}

/**
 * 驼峰转下划线
 * 例如：llmProvider → llm_provider
 */
function camelToSnake(camelStr) {
  if (!camelStr || typeof camelStr !== 'string') {
    return camelStr
  }

  return camelStr.replace(/([A-Z])/g, '_$1').toLowerCase().replace(/^_/, '')
}

/**
 * 将 Gradio 格式的配置转换为组件可用的格式
 * 原格式: { "agent_settings.llm_provider": "openai", ... }
 * 新格式: { llmProvider: "openai", ... }
 */
export function transformGradioConfig(gradioConfig) {
  if (!gradioConfig || typeof gradioConfig !== 'object') {
    return {}
  }

  const result = {}

  Object.keys(gradioConfig).forEach(key => {
    // 如果键包含点，只取最后一部分
    let fieldName = key
    if (key.includes('.')) {
      const parts = key.split('.')
      fieldName = parts[parts.length - 1]
    }

    // 下划线转驼峰
    const camelName = snakeToCamel(fieldName)
    result[camelName] = gradioConfig[key]
  })

  return result
}

/**
 * 合并默认配置和加载的配置
 * 确保所有必需的字段都有值
 */
export function mergeWithDefaults(loadedConfig, defaults) {
  if (!defaults || typeof defaults !== 'object') {
    return loadedConfig || {}
  }

  const result = { ...defaults }

  if (loadedConfig && typeof loadedConfig === 'object') {
    Object.keys(loadedConfig).forEach(key => {
      if (loadedConfig[key] !== undefined && loadedConfig[key] !== null) {
        // 确保字段名匹配，支持下划线和驼峰
        const camelKey = snakeToCamel(key)
        if (result.hasOwnProperty(camelKey) || result.hasOwnProperty(key)) {
          const targetKey = result.hasOwnProperty(camelKey) ? camelKey : key
          result[targetKey] = loadedConfig[key]
        }
      }
    })
  }

  return result
}

/**
 * 安全地获取配置值
 */
export function getConfigValue(config, key, defaultValue) {
  if (!config || typeof config !== 'object') {
    return defaultValue
  }

  const camelKey = snakeToCamel(key)

  if (config[key] !== undefined && config[key] !== null) {
    return config[key]
  }

  if (config[camelKey] !== undefined && config[camelKey] !== null) {
    return config[camelKey]
  }

  return defaultValue
}