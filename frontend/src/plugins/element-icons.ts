import { 
  User, 
  Document, 
  ChatDotRound, 
  ChatLineRound,
  Search, 
  Tickets, 
  Plus, 
  Position, 
  UploadFilled 
} from '@element-plus/icons-vue'
import type { App } from 'vue'

export default {
  install(app: App) {
    app.component('User', User)
    app.component('Document', Document)
    app.component('ChatDotRound', ChatDotRound)
    app.component('ChatLineRound', ChatLineRound)
    app.component('Search', Search)
    app.component('Tickets', Tickets)
    app.component('Plus', Plus)
    app.component('Position', Position)
    app.component('UploadFilled', UploadFilled)
  }
} 