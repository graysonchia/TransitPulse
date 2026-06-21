import { useState } from 'react'
import OverviewPage from './pages/OverviewPage'
import RidershipPage from './pages/RidershipPage'
import ForecastPage from './pages/ForecastPage'
import DelaysPage from './pages/DelaysPage'
import MLPage from './pages/MLPage'

const tabs = [
  ['overview', 'Overview'],
  ['ridership', 'Ridership'],
  ['forecast', 'Forecast'],
  ['delays', 'Delays'],
  ['ml', 'ML Insights'],
]

export default function App() {
  const [activeTab, setActiveTab] = useState('overview')
  const pages = {
    overview: <OverviewPage setActiveTab={setActiveTab} />,
    ridership: <RidershipPage setActiveTab={setActiveTab} />,
    forecast: <ForecastPage setActiveTab={setActiveTab} />,
    delays: <DelaysPage setActiveTab={setActiveTab} />,
    ml: <MLPage setActiveTab={setActiveTab} />,
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-slate-800/80 bg-[#07111f]/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-6 px-5 py-4 sm:px-8">
          <div>
            <div className="text-[1.6rem] font-extrabold leading-none text-white">
              Transit<span className="text-brand">Pulse</span>
            </div>
            <p className="mt-1 text-xs text-slate-400 sm:text-sm">Klang Valley Public Transport Analytics</p>
          </div>
          <div className="hidden text-right text-xs text-slate-500 sm:block">
            <div>Last updated</div>
            <div className="mt-1 text-slate-300">{new Date().toLocaleString()}</div>
          </div>
        </div>
        <nav className="mx-auto flex max-w-[1600px] overflow-x-auto px-5 sm:px-8">
          {tabs.map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setActiveTab(key)}
              className={`whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition ${
                activeTab === key
                  ? 'border-brand text-brand'
                  : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-[1600px] px-5 py-7 sm:px-8">{pages[activeTab]}</main>
    </div>
  )
}
