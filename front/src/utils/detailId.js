/**
 * Detail 页面 ID 生成工具
 *
 * 特性：
 * 1. 新开的 tab 生成随机 ID
 * 2. 不同 tab 保证 ID 不同
 * 3. 同一个 tab 刷新时，ID 与刷新前相同
 */

const DETAIL_ID_KEY = 'browser_use_detail_id'

/**
 * 生成随机 ID
 * 格式: {random}-{timestamp}
 */
function generateDetailID() {
  // 随机字符串（8位）
  const random = Math.random().toString(36).substring(2, 10)

  // 时间戳（16进制，缩短长度）
  const timestamp = Date.now().toString(36)

  // 组合 ID
  return `${random}-${timestamp}`
}

/**
 * 获取或创建 Detail ID
 * - 如果 sessionStorage 中已存在，返回现有 ID（刷新场景）
 * - 如果不存在，生成新 ID（新 tab 场景）
 * - 特殊处理：URL 中包含 _new_tab 参数时，强制生成新 ID
 */
export async function getOrCreateDetailID() {
  // 检查 URL 中是否有 _new_tab 参数（表示是新打开的标签页）
  // 注意：在 hash 模式下，查询参数在 hash 中，不在 search 中
  let isNewTab = false
  let urlParams = new URLSearchParams()

  // 方法 1: 尝试从 window.location.search 获取（history 模式）
  if (window.location.search) {
    urlParams = new URLSearchParams(window.location.search)
    isNewTab = urlParams.has('_new_tab')
    console.log('[DetailID] Found params in search:', window.location.search)
  }

  // 方法 2: 从 hash 中解析查询参数（hash 模式）
  if (!isNewTab && window.location.hash) {
    const hash = window.location.hash
    console.log('[DetailID] Hash:', hash)

    // hash 格式: #/detail?_new_tab=123
    const queryIndex = hash.indexOf('?')
    if (queryIndex !== -1) {
      const queryString = hash.substring(queryIndex + 1)
      console.log('[DetailID] Query string from hash:', queryString)
      urlParams = new URLSearchParams(queryString)
      isNewTab = urlParams.has('_new_tab')
    }
  }

  console.log('[DetailID] Is new tab param:', isNewTab)

  // 检查 sessionStorage 中是否已有 ID
  const existingID = sessionStorage.getItem(DETAIL_ID_KEY)

  if (existingID && !isNewTab) {
    console.log('[DetailID] Using existing ID:', existingID)
    return existingID
  }

  // 生成新 ID
  const newID = generateDetailID()
  console.log('[DetailID] Generated new ID:', newID, isNewTab ? '(forced for new tab via URL param)' : '')

  // 存储到 sessionStorage（tab 级别，刷新后保留）
  sessionStorage.setItem(DETAIL_ID_KEY, newID)

  // 清理 URL 中的 _new_tab 参数（避免刷新时重复生成）
  if (isNewTab) {
    urlParams.delete('_new_tab')
    const remainingParams = urlParams.toString()

    // 重建 hash
    const hashPath = window.location.hash.split('?')[0] // #/detail
    const newHash = remainingParams
      ? `${hashPath}?${remainingParams}`
      : hashPath

    console.log('[DetailID] Cleaning URL, new hash:', newHash)
    window.history.replaceState({}, '', `${window.location.pathname}${newHash}`)
  }

  return newID
}

/**
 * 获取当前 Detail ID（不创建新 ID）
 */
export function getCurrentDetailID() {
  return sessionStorage.getItem(DETAIL_ID_KEY)
}

/**
 * 清除 Detail ID（用于测试或手动重置）
 */
export function clearDetailID() {
  sessionStorage.removeItem(DETAIL_ID_KEY)
}

/**
 * 解析 Detail ID
 */
export function parseDetailID(id) {
  const parts = id.split('-')
  if (parts.length !== 2) {
    return null
  }

  return {
    random: parts[0],
    timestamp: parseInt(parts[1], 36),
    fullID: id
  }
}

export default {
  getOrCreateDetailID,
  getCurrentDetailID,
  clearDetailID,
  parseDetailID
}
