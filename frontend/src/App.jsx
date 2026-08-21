import { Link, NavLink, Route, Routes } from 'react-router-dom';
import ContestsPage from './pages/ContestsPage.jsx';
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
        <NavLink to="/swimmers">Пловцы</NavLink>
        <NavLink to="/entries">Заявки</NavLink>
        <NavLink to="/results">Результаты</NavLink>
      </nav>

      <main>
        <Routes>
          <Route path="/" element={<ContestsPage />} />
          <Route path="/contests" element={<ContestsPage />} />
          <Route path="/swimmers" element={<SwimmersPage />} />
          <Route path="/entries" element={<EntriesPage />} />
          <Route path="/entries/new" element={<EntryFormPage />} />
          <Route path="/results" element={<ResultsPage />} />
        </Routes>
      </main>
    </>
  );
}
