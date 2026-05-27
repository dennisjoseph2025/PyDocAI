import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import FeedbackModal from '../components/FeedbackModal';
import { useNavigate } from 'react-router-dom';

export default function FeedbackPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      <Navbar />
      <main className="flex-1 flex items-center justify-center py-12 px-6">
        <div className="w-full max-w-lg">
          <FeedbackModal onClose={() => navigate(-1)} />
        </div>
      </main>
      <Footer />
    </div>
  );
}