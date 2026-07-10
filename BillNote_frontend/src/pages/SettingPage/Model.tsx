import Provider from '@/components/Form/modelForm/Provider.tsx'
import { Outlet } from 'react-router-dom'
import ProxyConfig from '@/components/Form/DownloaderForm/ProxyConfig.tsx'

const Model = () => {
  return (
    <div className={'flex h-full min-h-0 bg-white'}>
      <div className={'flex-1/5 min-h-0 overflow-y-auto border-r border-neutral-200 p-2'}>
        <div className="mb-3">
          <ProxyConfig target="ai" />
        </div>
        <Provider></Provider>
      </div>
      <div className={'flex-4/5 min-h-0 overflow-y-auto'}>
        <Outlet />
      </div>
    </div>
  )
}
export default Model
