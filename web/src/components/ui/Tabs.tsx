"use client";

import { useState, useCallback, useId, type ReactNode } from "react";

interface TabItem {
  id: string;
  label: string;
  panel: ReactNode;
}

interface TabsProps {
  tabs: TabItem[];
  defaultTab?: string;
  /** Accessible label for the tablist (e.g. "Analytics sections") */
  ariaLabel: string;
  /** Optional class for the tablist container */
  className?: string;
}

const FOCUS_RING = "focus:outline-none focus-visible:ring-2 focus-visible:ring-[#8C302C] focus-visible:ring-offset-2";

export default function Tabs({ tabs, defaultTab, ariaLabel, className = "" }: TabsProps) {
  const baseId = useId();
  const firstTabId = tabs[0]?.id ?? "";
  const [activeId, setActiveId] = useState(defaultTab ?? firstTabId);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      const index = tabs.findIndex((t) => t.id === activeId);
      if (index === -1) return;

      let nextIndex = index;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        nextIndex = Math.min(index + 1, tabs.length - 1);
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        nextIndex = Math.max(index - 1, 0);
      } else if (e.key === "Home") {
        e.preventDefault();
        nextIndex = 0;
      } else if (e.key === "End") {
        e.preventDefault();
        nextIndex = tabs.length - 1;
      } else return;

      const nextTab = tabs[nextIndex];
      if (nextTab) {
        setActiveId(nextTab.id);
        const el = document.getElementById(`${baseId}-tab-${nextTab.id}`);
        el?.focus();
      }
    },
    [activeId, tabs, baseId]
  );

  return (
    <div className={className}>
      <div
        role="tablist"
        aria-label={ariaLabel}
        onKeyDown={handleKeyDown}
        className="flex flex-wrap gap-1 border-b-2 border-[#d1d5db] mb-6"
      >
        {tabs.map((tab) => {
          const isActive = tab.id === activeId;
          const tabId = `${baseId}-tab-${tab.id}`;
          const panelId = `${baseId}-panel-${tab.id}`;

          return (
            <button
              key={tab.id}
              id={tabId}
              role="tab"
              tabIndex={isActive ? 0 : -1}
              aria-selected={isActive}
              aria-controls={panelId}
              onClick={() => setActiveId(tab.id)}
              className={`
                min-h-[44px] min-w-[44px] px-5 py-3 text-xs font-bold uppercase tracking-[0.2em] font-mono
                transition-colors -mb-[2px]
                ${FOCUS_RING}
                ${isActive
                  ? "border-b-2 border-[#8C302C] text-[#8C302C] bg-transparent"
                  : "text-[#5c5a57] hover:text-[#234058] hover:bg-[#234058]/5"}
              `}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {tabs.map((tab) => {
        const isActive = tab.id === activeId;
        const panelId = `${baseId}-panel-${tab.id}`;
        const tabId = `${baseId}-tab-${tab.id}`;

        return (
          <div
            key={tab.id}
            id={panelId}
            role="tabpanel"
            aria-labelledby={tabId}
            hidden={!isActive}
            className={isActive ? "block" : "hidden"}
          >
            {tab.panel}
          </div>
        );
      })}
    </div>
  );
}
