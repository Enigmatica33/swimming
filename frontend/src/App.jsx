import { Link, NavLink, Route, Routes } from 'react-router-dom';
import ContestsPage from './pages/ContestsPage.jsx';
import CoachesPage from './pages/CoachesPage.jsx';
import SwimmersPage from './pages/SwimmersPage.jsx';
import EntriesPage from './pages/EntriesPage.jsx';
import EntryFormPage from './pages/EntryFormPage.jsx';
import ResultsPage from './pages/ResultsPage.jsx';

export default function App() {
  return (
    <>
      <nav>
        <Link to="/" style={{ fontWeight: 700 }}>
          🏊 Плавание
        </Link>
        <NavLink to="/contests">Соревнования</NavLink>
        <NavLink to="/coaches">Тренеры</NavLink>
        <NavLink to="/swimmers">Пловцы</NavLink>
        <NavLink to="/entries">Заявки</NavLink>
      </nav>

      <main>
        <Routes>
          <Route path="/" element={<ContestsPage />} />
          <Route path="/contests" element={<ContestsPage />} />
          <Route path="/coaches" element={<CoachesPage />} />
          <Route path="/swimmers" element={<SwimmersPage />} />
          <Route path="/entries" element={<EntriesPage />} />
          <Route path="/entries/new" element={<EntryFormPage />} />
          <Route path="/results/:id" element={<ResultsPage />} />
        </Routes>
      </main>
    </>
  );
}
