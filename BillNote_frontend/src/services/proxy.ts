import request from '@/utils/request'

export interface ProxySectionConfig {
  enabled: boolean
  url: string
}

export interface ProxyConfig {
  ai: ProxySectionConfig
  youtube: ProxySectionConfig
  effective: {
    ai: string
    youtube: string
  }
}

export const getProxyConfig = async (): Promise<ProxyConfig> => {
  return await request.get('/proxy_config')
}

export const updateProxyConfig = async (data: Partial<{
  ai: ProxySectionConfig
  youtube: ProxySectionConfig
}>): Promise<ProxyConfig> => {
  return await request.post('/proxy_config', data)
}
