"use client";

import { useEffect, useState } from "react";
import styles from "./page.module.css";

interface Machine {
  id: number;
  marca: string;
  modelo: string;
  ano: string;
  horasMotor: string;
  horasRotor: string;
  tipoPlataforma: string;
  preco: string;
  localizacao: string;
  url: string;
  categoria: string;
}

export default function Home() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState(true);

  // Filtros
  const [search, setSearch] = useState("");
  const [categoria, setCategoria] = useState("Todas");
  const [anoMin, setAnoMin] = useState("");

  useEffect(() => {
    fetch("/api/machines")
      .then((res) => res.json())
      .then((data) => {
        if (data.machines) {
          setMachines(data.machines);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Erro ao carregar máquinas", err);
        setLoading(false);
      });
  }, []);

  const filteredMachines = machines.filter((m) => {
    const searchMatch =
      m.marca.toLowerCase().includes(search.toLowerCase()) ||
      m.modelo.toLowerCase().includes(search.toLowerCase());
      
    const catMatch =
      categoria === "Todas" || m.categoria.toLowerCase() === categoria.toLowerCase();
      
    const anoMatch = anoMin ? parseInt(m.ano) >= parseInt(anoMin) : true;

    // Ignorar linhas vazias
    if (!m.marca && !m.modelo) return false;

    return searchMatch && catMatch && anoMatch;
  });

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1 className={styles.title}>Chopper House Aut</h1>
        <p className={styles.subtitle}>
          Inteligência de Mercado de Forrageiras Europeias
        </p>
      </header>

      <div className={styles.layout}>
        {/* SIDEBAR DE FILTROS */}
        <aside className={styles.sidebar}>
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>Busca Global</label>
            <input
              type="text"
              placeholder="Buscar marca ou modelo..."
              className={styles.input}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>Categoria</label>
            <select
              className={styles.select}
              value={categoria}
              onChange={(e) => setCategoria(e.target.value)}
            >
              <option value="Todas">Todas</option>
              <option value="Forrageira">Forrageiras</option>
              <option value="Plataforma">Plataformas</option>
            </select>
          </div>

          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>Ano Mínimo</label>
            <input
              type="number"
              placeholder="Ex: 2018"
              className={styles.input}
              value={anoMin}
              onChange={(e) => setAnoMin(e.target.value)}
            />
          </div>
        </aside>

        {/* GRID DE RESULTADOS */}
        <div className={styles.grid}>
          {loading ? (
            <div className={styles.loading}>Minerando dados da Europa...</div>
          ) : filteredMachines.length === 0 ? (
            <div className={styles.noResults}>
              Nenhuma máquina encontrada com estes filtros.
            </div>
          ) : (
            filteredMachines.map((m) => (
              <div key={m.id} className={styles.card}>
                <div className={styles.cardHeader}>
                  <h2 className={styles.cardTitle}>
                    {m.marca} {m.modelo}
                  </h2>
                  <span className={styles.badge}>{m.categoria || "N/A"}</span>
                </div>

                <div className={styles.cardInfo}>
                  <div className={styles.infoRow}>
                    <span>Ano de Fabricação</span>
                    <strong>{m.ano || "-"}</strong>
                  </div>
                  {m.horasMotor && (
                    <div className={styles.infoRow}>
                      <span>Horas de Motor</span>
                      <strong>{m.horasMotor} h</strong>
                    </div>
                  )}
                  {m.horasRotor && (
                    <div className={styles.infoRow}>
                      <span>Horas de Rotor</span>
                      <strong>{m.horasRotor} h</strong>
                    </div>
                  )}
                  {m.tipoPlataforma && (
                    <div className={styles.infoRow}>
                      <span>Plataforma Inclusa</span>
                      <strong>{m.tipoPlataforma}</strong>
                    </div>
                  )}
                  <div className={styles.infoRow}>
                    <span>Localização</span>
                    <strong>{m.localizacao || "Europa"}</strong>
                  </div>
                </div>

                <div className={styles.price}>
                  {m.preco && m.preco !== "N/A" ? m.preco : "Sob Consulta"}
                </div>

                <a
                  href={m.url}
                  target="_blank"
                  rel="noreferrer"
                  className={styles.link}
                >
                  Acessar Anúncio
                </a>
              </div>
            ))
          )}
        </div>
      </div>
    </main>
  );
}
