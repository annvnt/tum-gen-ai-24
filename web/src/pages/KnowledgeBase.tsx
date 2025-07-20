// This is a React Router version placeholder
// The actual KnowledgeBase page is in app/knowledge-base/page.tsx for Next.js

export default function KnowledgeBase() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Knowledge Base</h1>
        <p className="text-gray-600 mb-8">
          This page is using React Router. For Next.js, use /knowledge-base route.
        </p>
        <a 
          href="/"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 inline-block"
        >
          Go back home
        </a>
      </div>
    </div>
  );
}