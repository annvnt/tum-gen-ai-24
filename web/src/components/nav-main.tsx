"use client"

import { MailIcon, PlusCircleIcon, MoreHorizontalIcon, type LucideIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export function NavMain({
  items,
}: {
  items: {
    title: string
    url: string
    icon?: LucideIcon
  }[]
}) {
  return (
    <SidebarGroup>
      <SidebarGroupContent className="flex flex-col gap-2">
        <SidebarMenu>
          <SidebarMenuItem className="flex items-center gap-2">
            <Button
              // tooltip="Quick Create"// bg-secondary text-slate-50 duration-200 ease-linear hover:bg-slate-900/90 hover:text-slate-50 active:bg-slate-900/90 active:text-slate-50 dark:bg-slate-50 dark:text-slate-900 dark:hover:bg-slate-50/90 dark:hover:text-slate-900 dark:active:bg-slate-50/90 dark:active:text-slate-900"
              // variant="primary"
              className="min-w-8"
            >

              <PlusCircleIcon />
              <span>New Project</span>
            </Button>
            <Button
              size="icon"
              className="h-9 w-9 shrink-0 group-data-[collapsible=icon]:opacity-0"
              variant="outline"
            >
              <MailIcon />
              <span className="sr-only">Inbox</span>
            </Button>
          </SidebarMenuItem>
        </SidebarMenu>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton tooltip={item.title}>
                {item.icon && <item.icon />}
                <span>{item.title}</span>
              </SidebarMenuButton>

            </SidebarMenuItem>
          ))}
        </SidebarMenu>

          <SidebarMenuButton className="text-sidebar-foreground/70">
            <MoreHorizontalIcon className="text-sidebar-foreground/70" />
            <span>All projects</span>
          </SidebarMenuButton>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
