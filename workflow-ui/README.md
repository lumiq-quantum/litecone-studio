# Workflow Management UI

A modern, beautiful React-based web application for managing the Workflow Orchestration System.

## Tech Stack

- **React 18+** with TypeScript
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - High-quality component library
- **Radix UI** - Accessible UI primitives
- **TanStack Query** - Server state management
- **React Router v6** - Client-side routing
- **Zustand** - Lightweight state management
- **Axios** - HTTP client
- **Framer Motion** - Animations
- **Lucide React** - Icon library

## Getting Started

### Prerequisites

- Node.js 20.19+ or 22.12+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Copy the environment file:
```bash
cp .env.example .env
```

3. Update the `.env` file with your API URL:
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_POLLING_INTERVAL=2000
VITE_APP_NAME=Workflow Manager
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building for Production

Build the application:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint errors
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check code formatting
- `npm run type-check` - Run TypeScript type checking
- `npm test` - Run unit tests
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Run tests with coverage report

## Project Structure

```
workflow-ui/
├── src/
│   ├── main.tsx           # Application entry point
│   ├── App.tsx            # Root component
│   ├── index.css          # Global styles
│   ├── lib/               # Utilities
│   │   └── utils.ts       # Helper functions
│   ├── pages/             # Page components
│   ├── components/        # Reusable components
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API services
│   ├── types/             # TypeScript types
│   ├── utils/             # Utility functions
│   └── store/             # State management
├── public/                # Static assets
├── .env                   # Environment variables
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind configuration
└── tsconfig.json          # TypeScript configuration
```

## Features

- 🎨 Modern, beautiful UI with Tailwind CSS
- 🔄 Real-time workflow execution monitoring
- 📊 Visual workflow graphs
- 🚀 Fast development with Vite HMR
- 💪 Type-safe with TypeScript strict mode
- ♿ Accessible components with Radix UI
- 🎭 Smooth animations with Framer Motion
- 📱 Fully responsive design

## Configuration

### Environment Variables

The application uses the following environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000/api/v1` | Yes |
| `VITE_POLLING_INTERVAL` | Polling interval for real-time updates (ms) | `2000` | No |
| `VITE_APP_NAME` | Application name displayed in UI | `Workflow Manager` | No |

Create a `.env` file in the root directory:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_POLLING_INTERVAL=2000
VITE_APP_NAME=Workflow Manager
```

### Path Aliases

The project uses `@/` as an alias for the `src/` directory:

```typescript
import { cn } from '@/lib/utils';
```

### API Proxy

The Vite dev server is configured to proxy API requests to the backend:

```typescript
// Requests to /api/* will be proxied to http://localhost:8000/api/*
```

## Code Quality

The project uses:
- **ESLint** for code linting
- **Prettier** for code formatting
- **TypeScript** in strict mode for type safety
- **Vitest** for unit and integration testing

Run checks before committing:
```bash
npm run lint
npm run format:check
npm run type-check
npm test
```

## User Guide

### Managing Agents

1. **View Agents**: Navigate to the Agents page to see all registered agents
2. **Create Agent**: Click the "Add Agent" button and fill in the form:
   - Name: Unique identifier for the agent
   - URL: Agent endpoint URL (must start with http:// or https://)
   - Description: Optional description
   - Timeout: Request timeout in seconds
   - Retry Configuration: Max retries and retry delay
3. **Test Agent**: Click "Test Health" to verify agent connectivity
4. **Edit/Delete**: Use the action buttons on each agent card

### Creating Workflows

1. **Navigate to Workflows**: Click "Workflows" in the sidebar
2. **Create New Workflow**: Click "Create Workflow" button
3. **Define Workflow**:
   - Enter workflow name and description
   - Use the JSON editor to define workflow steps
   - The visual preview updates in real-time
4. **Validate**: The editor will highlight any syntax or validation errors
5. **Save**: Click "Save" to create the workflow

### Executing Workflows

1. **Select Workflow**: Navigate to the workflow detail page
2. **Click Execute**: Click the "Execute" button
3. **Provide Input**: Enter input data in JSON format
4. **Select Version**: Choose which version to execute (defaults to latest)
5. **Start Execution**: Click "Execute" to start the workflow
6. **Monitor Progress**: View real-time execution status in the execution graph

### Monitoring Runs

1. **View Runs**: Navigate to the Runs page
2. **Filter Runs**: Use filters to find specific runs by status, workflow, or date
3. **View Details**: Click on a run to see detailed execution information
4. **Inspect Steps**: Click on steps in the execution graph to view input/output data
5. **Retry Failed Runs**: Click "Retry" on failed runs to re-execute from the failed step
6. **Export Results**: Download run results as JSON

## Troubleshooting

### Development Server Won't Start

**Problem**: `npm run dev` fails or shows errors

**Solutions**:
- Ensure Node.js version is 20.19+ or 22.12+
- Delete `node_modules` and `package-lock.json`, then run `npm install` again
- Check if port 5173 is already in use
- Clear Vite cache: `rm -rf node_modules/.vite`

### API Connection Errors

**Problem**: "Unable to connect to the server" or network errors

**Solutions**:
- Verify the backend API is running
- Check `VITE_API_URL` in `.env` file matches your backend URL
- Ensure CORS is properly configured on the backend
- Check browser console for detailed error messages
- Try accessing the API URL directly in your browser

### Build Errors

**Problem**: `npm run build` fails with TypeScript errors

**Solutions**:
- Run `npm run type-check` to see all type errors
- Ensure all dependencies are installed: `npm install`
- Check for missing type definitions
- Update TypeScript: `npm install -D typescript@latest`

### Tests Failing

**Problem**: Tests fail when running `npm test`

**Solutions**:
- Clear test cache: `npx vitest --clearCache`
- Ensure all dependencies are installed
- Check for environment-specific issues
- Run tests in watch mode for debugging: `npm run test:watch`

### Styling Issues

**Problem**: Tailwind classes not working or styles not applying

**Solutions**:
- Restart the dev server
- Check if Tailwind is properly configured in `tailwind.config.js`
- Ensure PostCSS is configured correctly
- Clear browser cache and hard reload (Ctrl+Shift+R)

### Performance Issues

**Problem**: Application is slow or unresponsive

**Solutions**:
- Check browser console for errors or warnings
- Reduce polling interval in `.env` file
- Clear browser cache and local storage
- Check network tab for slow API requests
- Ensure backend API is responding quickly

### Common Error Messages

#### "Failed to fetch"
- Backend API is not running or not accessible
- Check CORS configuration on backend
- Verify API URL in environment variables

#### "Validation error"
- Check input data format matches expected schema
- Review error messages for specific field issues
- Ensure all required fields are provided

#### "Resource not found"
- The requested item may have been deleted
- Refresh the page to update the list
- Check if you have the correct ID/URL

## Browser Support

The application supports modern browsers:
- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests and linting: `npm test && npm run lint`
5. Commit your changes: `git commit -am 'Add new feature'`
6. Push to the branch: `git push origin feature/my-feature`
7. Create a Pull Request

## License

MIT
