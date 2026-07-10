import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { getProxyConfig, updateProxyConfig, type ProxySectionConfig } from '@/services/proxy'

type ProxyKey = 'ai' | 'youtube'

interface ProxySectionProps {
  title: string
  description: string
  value: ProxySectionConfig
  effective: string
  saving: boolean
  onChange: (value: ProxySectionConfig) => void
  onSave: () => void
}

const ProxySection = ({
  title,
  description,
  value,
  effective,
  saving,
  onChange,
  onSave,
}: ProxySectionProps) => {
  const fromEnv = !value.enabled && !!effective

  return (
    <div className="flex flex-col gap-2 rounded border border-neutral-200 p-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{title}</span>
        <Switch
          checked={value.enabled}
          onCheckedChange={enabled => onChange({ ...value, enabled })}
        />
      </div>
      <p className="text-xs text-gray-400">{description}</p>
      <Input
        placeholder="http://host.docker.internal:7897"
        value={value.url}
        disabled={!value.enabled}
        onChange={e => onChange({ ...value, url: e.target.value })}
        className="text-sm"
      />
      {fromEnv && <p className="text-xs text-amber-600">当前生效（来自环境变量）：{effective}</p>}
      {value.enabled && effective && <p className="text-xs text-green-600">当前生效：{effective}</p>}
      <Button size="sm" onClick={onSave} disabled={saving}>
        {saving ? '保存中…' : '保存代理配置'}
      </Button>
    </div>
  )
}

const emptyProxy = (): ProxySectionConfig => ({ enabled: false, url: '' })

const proxyMeta: Record<ProxyKey, { title: string; description: string }> = {
  ai: {
    title: 'AI 代理',
    description: '作用于 OpenAI、Groq 与兼容 OpenAI 的模型接口。',
  },
  youtube: {
    title: 'YouTube 代理',
    description: '作用于 YouTube 字幕获取与 yt-dlp 下载。',
  },
}

interface ProxyConfigProps {
  target?: ProxyKey
}

const ProxyConfig = ({ target }: ProxyConfigProps) => {
  const [ai, setAi] = useState<ProxySectionConfig>(emptyProxy)
  const [youtube, setYoutube] = useState<ProxySectionConfig>(emptyProxy)
  const [effective, setEffective] = useState<Record<ProxyKey, string>>({ ai: '', youtube: '' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<ProxyKey | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        const cfg = await getProxyConfig()
        setAi(cfg.ai)
        setYoutube(cfg.youtube)
        setEffective(cfg.effective)
      } catch {
        /* 拦截器已 toast */
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const handleSave = async (key: ProxyKey) => {
    const value = key === 'ai' ? ai : youtube
    if (value.enabled && !value.url.trim()) {
      toast.error('请填写代理地址，或关闭代理开关')
      return
    }

    setSaving(key)
    try {
      const cfg = await updateProxyConfig({
        [key]: { enabled: value.enabled, url: value.url.trim() },
      })
      setAi(cfg.ai)
      setYoutube(cfg.youtube)
      setEffective(cfg.effective)
      toast.success('代理配置已保存')
    } catch {
      /* 拦截器已 toast */
    } finally {
      setSaving(null)
    }
  }

  if (loading) {
    return <div className="text-xs text-gray-400">加载代理配置…</div>
  }

  return (
    <div className="flex flex-col gap-3">
      {(!target || target === 'ai') && (
        <ProxySection
          title={proxyMeta.ai.title}
          description={proxyMeta.ai.description}
          value={ai}
          effective={effective.ai}
          saving={saving === 'ai'}
          onChange={setAi}
          onSave={() => handleSave('ai')}
        />
      )}
      {(!target || target === 'youtube') && (
        <ProxySection
          title={proxyMeta.youtube.title}
          description={proxyMeta.youtube.description}
          value={youtube}
          effective={effective.youtube}
          saving={saving === 'youtube'}
          onChange={setYoutube}
          onSave={() => handleSave('youtube')}
        />
      )}
    </div>
  )
}

export default ProxyConfig
