import React, { useState, useEffect } from 'react';
import { MapPin, Activity, Calendar, Star, Compass, Download, Zap, Users, Filter, Check } from 'lucide-react';

const HypeMap = () => {
  const [activeFilter, setActiveFilter] = useState('todos');
  const [places, setPlaces] = useState([
    { id: 1, name: 'Mercado Novo', type: 'bar', heat: 85, trend: 'up', coords: { x: 30, y: 40 } },
    { id: 2, name: 'Sapucaí', type: 'bar', heat: 92, trend: 'up', coords: { x: 45, y: 35 } },
    { id: 3, name: 'Savassi', type: 'restaurante', heat: 60, trend: 'down', coords: { x: 60, y: 65 } },
    { id: 4, name: 'Mineirão', type: 'show', heat: 98, trend: 'up', coords: { x: 20, y: 20 } },
    { id: 5, name: 'Praça da Liberdade', type: 'restaurante', heat: 45, trend: 'stable', coords: { x: 55, y: 50 } },
    { id: 6, name: 'Rua Alberto Cintra', type: 'bar', heat: 75, trend: 'up', coords: { x: 75, y: 30 } }
  ]);

  // Simulação de tempo real
  useEffect(() => {
    const interval = setInterval(() => {
      setPlaces(currentPlaces =>
        currentPlaces.map(place => {
          // Variação aleatória entre -5 e +5
          const variation = Math.floor(Math.random() * 11) - 5;
          let newHeat = place.heat + variation;

          // Mantém entre 10 e 100
          if (newHeat > 100) newHeat = 100;
          if (newHeat < 10) newHeat = 10;

          let newTrend = variation > 0 ? 'up' : (variation < 0 ? 'down' : 'stable');

          return { ...place, heat: newHeat, trend: newTrend };
        })
      );
    }, 3000); // Atualiza a cada 3 segundos

    return () => clearInterval(interval);
  }, []);

  const filteredPlaces = activeFilter === 'todos'
    ? places
    : places.filter(p => p.type === activeFilter);

  // Função auxiliar para cor baseada no calor
  const getHeatColor = (heat) => {
    if (heat >= 80) return 'text-rose-500';
    if (heat >= 50) return 'text-orange-500';
    return 'text-emerald-500';
  };

  const getHeatBg = (heat) => {
    if (heat >= 80) return 'bg-rose-500';
    if (heat >= 50) return 'bg-orange-500';
    return 'bg-emerald-500';
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-rose-500 selection:text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full backdrop-blur-md bg-slate-950/80 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            {/* Logo */}
            <div className="flex-shrink-0 flex items-center gap-2">
              <Compass className="h-8 w-8 text-rose-500" />
              <span className="font-bold text-2xl tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-rose-500 to-rose-400">
                HypeMap
              </span>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex space-x-8">
              <a href="#mapa" className="text-slate-300 hover:text-white transition-colors text-sm font-medium">Mapa</a>
              <a href="#destaques" className="text-slate-300 hover:text-white transition-colors text-sm font-medium">Destaques</a>
              <a href="#planos" className="text-slate-300 hover:text-white transition-colors text-sm font-medium">Planos</a>
            </nav>

            {/* CTA Button */}
            <div className="flex items-center">
              <button className="flex items-center gap-2 bg-rose-600 hover:bg-rose-700 text-white px-5 py-2.5 rounded-full font-medium transition-all shadow-[0_0_15px_rgba(225,29,72,0.5)] hover:shadow-[0_0_25px_rgba(225,29,72,0.7)]">
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline">Baixar App</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
        {/* Background Effects */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-rose-600/20 rounded-full blur-[120px] pointer-events-none"></div>
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[100px] pointer-events-none"></div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8">
            Descubra a cidade em <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-400 to-rose-600">
              tempo real
            </span>
          </h1>

          <p className="mt-4 text-xl md:text-2xl text-slate-300 max-w-3xl mx-auto mb-10 font-light">
            Veja a movimentação dos melhores bares, restaurantes e eventos de Belo Horizonte agora mesmo. Não perca tempo e escolha o melhor rolê.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button className="w-full sm:w-auto px-8 py-4 bg-rose-600 hover:bg-rose-700 text-white rounded-full font-bold text-lg transition-all shadow-[0_0_20px_rgba(225,29,72,0.6)] hover:shadow-[0_0_30px_rgba(225,29,72,0.8)] hover:-translate-y-1">
              Explorar o Mapa
            </button>
            <button className="w-full sm:w-auto px-8 py-4 bg-slate-800 hover:bg-slate-700 text-white rounded-full font-bold text-lg border border-slate-700 transition-all">
              Ver Destaques
            </button>
          </div>
        </div>
      </section>

      {/* Seção Interativa - O Mapa */}
      <section id="mapa" className="py-20 bg-slate-900 border-y border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Os lugares mais <span className="text-rose-500">badalados</span> agora
            </h2>
            <p className="text-slate-400">Dados atualizados em tempo real de Belo Horizonte</p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">

            {/* Tabela / Lista Interativa */}
            <div className="lg:col-span-1 bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col h-[600px]">

              {/* Filtros */}
              <div className="flex flex-wrap gap-2 mb-6">
                <button
                  onClick={() => setActiveFilter('todos')}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${activeFilter === 'todos' ? 'bg-rose-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
                >
                  Todos
                </button>
                <button
                  onClick={() => setActiveFilter('bar')}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-1 ${activeFilter === 'bar' ? 'bg-rose-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
                >
                  Bares
                </button>
                <button
                  onClick={() => setActiveFilter('restaurante')}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-1 ${activeFilter === 'restaurante' ? 'bg-rose-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
                >
                  Restaurantes
                </button>
                <button
                  onClick={() => setActiveFilter('show')}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-1 ${activeFilter === 'show' ? 'bg-rose-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
                >
                  Shows
                </button>
              </div>

              {/* Tabela de Rankings */}
              <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-3">
                {filteredPlaces.sort((a,b) => b.heat - a.heat).map((place, index) => (
                  <div key={place.id} className="flex items-center justify-between p-4 bg-slate-900 rounded-xl border border-slate-800 hover:border-slate-700 transition-colors group">
                    <div className="flex items-center gap-4">
                      <div className="text-xl font-bold text-slate-500 w-6">{index + 1}</div>
                      <div>
                        <h4 className="font-bold text-white group-hover:text-rose-400 transition-colors">{place.name}</h4>
                        <span className="text-xs text-slate-400 capitalize">{place.type}</span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end">
                      <div className="flex items-center gap-1">
                        <Activity className={`w-4 h-4 ${getHeatColor(place.heat)}`} />
                        <span className={`font-bold ${getHeatColor(place.heat)}`}>{place.heat}%</span>
                      </div>
                      <div className="w-16 h-1.5 bg-slate-800 rounded-full mt-2 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ease-out ${getHeatBg(place.heat)}`}
                          style={{ width: `${place.heat}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Representação do Mapa */}
            <div className="lg:col-span-2 relative bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden h-[600px] flex items-center justify-center">

              {/* Grid background simulando ruas/mapa */}
              <div className="absolute inset-0 opacity-20"
                   style={{ backgroundImage: 'radial-gradient(#475569 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
              </div>

              {/* Glow effects no fundo do mapa */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-40">
                <div className="w-full h-full bg-gradient-to-tr from-slate-900 via-transparent to-slate-900"></div>
              </div>

              {/* Pins do Mapa */}
              {places.map(place => {
                // Se estiver filtrado, diminui a opacidade se não for o tipo selecionado
                const isVisible = activeFilter === 'todos' || place.type === activeFilter;

                return (
                  <div
                    key={`pin-${place.id}`}
                    className={`absolute transform -translate-x-1/2 -translate-y-1/2 transition-all duration-700 ease-in-out ${isVisible ? 'opacity-100 scale-100' : 'opacity-20 scale-75'}`}
                    style={{ left: `${place.coords.x}%`, top: `${place.coords.y}%`, zIndex: isVisible ? 10 : 1 }}
                  >
                    {/* Efeito de Pulso Baseado no Movimento */}
                    <div className="relative">
                      {place.heat > 70 && (
                        <div className={`absolute -inset-4 ${getHeatBg(place.heat)} rounded-full opacity-20 animate-ping`}
                             style={{ animationDuration: `${3 - (place.heat/50)}s` }}></div>
                      )}
                      <div className={`absolute -inset-2 ${getHeatBg(place.heat)} rounded-full opacity-30 blur-sm`}></div>

                      {/* O Pin */}
                      <div className={`relative flex items-center justify-center w-10 h-10 ${getHeatBg(place.heat)} rounded-full text-white shadow-lg border-2 border-slate-950 cursor-pointer hover:scale-110 transition-transform`}>
                        <MapPin className="w-5 h-5" />
                      </div>

                      {/* Tooltip do Pin */}
                      <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 bg-slate-900 border border-slate-700 text-white text-xs px-3 py-1.5 rounded-lg shadow-xl whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="font-bold">{place.name}</span> • {place.heat}%
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Card Flutuante de Simulação de Funcionalidade */}
              <div className="absolute bottom-6 right-6 w-72 bg-slate-950/90 backdrop-blur-md border border-slate-700 rounded-2xl shadow-2xl p-5 z-20 transform transition-transform hover:-translate-y-2">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-bold text-lg text-white">Rua Sapucaí</h3>
                    <p className="text-slate-400 text-xs">Polo Gastronômico</p>
                  </div>
                  <div className="bg-rose-500/20 text-rose-500 px-2 py-1 rounded-md text-xs font-bold flex items-center gap-1 border border-rose-500/30">
                    <Zap className="w-3 h-3" />
                    Alta
                  </div>
                </div>

                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-300">Nível de Movimentação</span>
                    <span className="text-rose-500 font-bold">92%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-orange-500 to-rose-600 rounded-full w-[92%]"></div>
                  </div>
                </div>

                <div>
                  <p className="text-xs text-slate-400 mb-2 uppercase font-semibold tracking-wider">Melhores eventos hoje</p>
                  <div className="space-y-2">
                    <div className="flex items-center gap-3 bg-slate-900 p-2 rounded-lg border border-slate-800">
                      <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                        <Calendar className="w-4 h-4" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-white">Samba da Meia Noite</p>
                        <p className="text-xs text-slate-400">20:00 • Entrada Gratuita</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </section>

      {/* Seção de Funcionalidades */}
      <section id="destaques" className="py-24 bg-slate-950 relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-rose-600/10 rounded-full blur-[100px] pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none"></div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-16 max-w-3xl mx-auto">
            <h2 className="text-3xl md:text-5xl font-bold mb-6">
              Por que usar o <span className="text-rose-500">HypeMap?</span>
            </h2>
            <p className="text-xl text-slate-400 font-light">
              Nossa tecnologia conecta você às melhores experiências da cidade, eliminando adivinhações e surpresas desagradáveis.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-slate-900 border border-slate-800 p-8 rounded-3xl hover:border-rose-500/50 transition-colors group">
              <div className="w-14 h-14 bg-rose-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Activity className="w-7 h-7 text-rose-500" />
              </div>
              <h3 className="text-2xl font-bold mb-4 text-white">Movimento em Tempo Real</h3>
              <p className="text-slate-400 leading-relaxed">
                Nossos mapas de calor mostram exatamente onde está a ação. Evite lugares vazios ou lotados demais, baseando sua decisão em dados atualizados ao vivo.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-slate-900 border border-slate-800 p-8 rounded-3xl hover:border-rose-500/50 transition-colors group">
              <div className="w-14 h-14 bg-rose-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Calendar className="w-7 h-7 text-rose-500" />
              </div>
              <h3 className="text-2xl font-bold mb-4 text-white">Eventos e Atrações</h3>
              <p className="text-slate-400 leading-relaxed">
                Tenha a agenda completa da cidade na palma da mão. De shows underground a grandes festivais, reunimos todas as opções de lazer em um único lugar.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-slate-900 border border-slate-800 p-8 rounded-3xl hover:border-rose-500/50 transition-colors group">
              <div className="w-14 h-14 bg-rose-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Star className="w-7 h-7 text-rose-500" />
              </div>
              <h3 className="text-2xl font-bold mb-4 text-white">Indicações Personalizadas</h3>
              <p className="text-slate-400 leading-relaxed">
                Descubra novos picos que combinam exatamente com a sua vibe. Nosso algoritmo aprende suas preferências para sugerir o rolê perfeito para a sua noite.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Seção de Planos de Assinatura */}
      <section id="planos" className="py-24 bg-slate-900 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4">Escolha o seu <span className="text-rose-500">Hype</span></h2>
            <p className="text-xl text-slate-400">Planos que cabem no seu bolso para você curtir a cidade sem limites.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto items-center">

            {/* Plano Básico */}
            <div className="bg-slate-950 border border-slate-800 rounded-3xl p-8 hover:border-slate-600 transition-colors">
              <h3 className="text-xl font-bold text-slate-300 mb-2">Básico</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-extrabold">R$ 2</span>
                <span className="text-slate-500">/mês</span>
              </div>
              <p className="text-slate-400 text-sm mb-6 pb-6 border-b border-slate-800">Essencial para quem quer descobrir a cidade.</p>

              <ul className="space-y-4 mb-8">
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-emerald-500 shrink-0" />
                  <span className="text-slate-300 text-sm">Acesso aos mapas da cidade</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-emerald-500 shrink-0" />
                  <span className="text-slate-300 text-sm">Lista de estabelecimentos</span>
                </li>
              </ul>

              <button className="w-full py-3 rounded-xl font-bold text-slate-300 bg-slate-800 hover:bg-slate-700 transition-colors">
                Assinar Básico
              </button>
            </div>

            {/* Plano Hype (Destaque) */}
            <div className="relative bg-slate-950 border-2 border-rose-500 rounded-3xl p-8 transform md:-translate-y-4 shadow-[0_0_40px_rgba(225,29,72,0.15)]">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-gradient-to-r from-rose-600 to-rose-400 text-white px-4 py-1 rounded-full text-sm font-bold shadow-lg">
                Mais Popular
              </div>

              <h3 className="text-xl font-bold text-rose-400 mb-2">Hype</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-5xl font-extrabold text-white">R$ 5</span>
                <span className="text-slate-500">/mês</span>
              </div>
              <p className="text-slate-400 text-sm mb-6 pb-6 border-b border-slate-800">Perfeito para quem não quer perder tempo.</p>

              <ul className="space-y-4 mb-8">
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-rose-500 shrink-0" />
                  <span className="text-slate-200 text-sm font-medium">Tudo do plano Básico</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-rose-500 shrink-0" />
                  <span className="text-slate-200 text-sm font-medium">Nível de movimentação em tempo real</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-rose-500 shrink-0" />
                  <span className="text-slate-200 text-sm font-medium">Filtros avançados (Bares, Shows, etc)</span>
                </li>
              </ul>

              <button className="w-full py-4 rounded-xl font-bold text-white bg-rose-600 hover:bg-rose-700 shadow-[0_0_15px_rgba(225,29,72,0.4)] transition-all">
                Assinar Hype
              </button>
            </div>

            {/* Plano VIP */}
            <div className="bg-slate-950 border border-slate-800 rounded-3xl p-8 hover:border-slate-600 transition-colors">
              <h3 className="text-xl font-bold text-indigo-400 mb-2">VIP</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-extrabold">R$ 10</span>
                <span className="text-slate-500">/mês</span>
              </div>
              <p className="text-slate-400 text-sm mb-6 pb-6 border-b border-slate-800">A experiência definitiva da vida noturna.</p>

              <ul className="space-y-4 mb-8">
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-indigo-400 shrink-0" />
                  <span className="text-slate-300 text-sm">Tudo do plano Hype</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-indigo-400 shrink-0" />
                  <span className="text-slate-300 text-sm">Acesso a eventos exclusivos</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-indigo-400 shrink-0" />
                  <span className="text-slate-300 text-sm">Promoções em parceiros</span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-indigo-400 shrink-0" />
                  <span className="text-slate-300 text-sm">Zero anúncios</span>
                </li>
              </ul>

              <button className="w-full py-3 rounded-xl font-bold text-white bg-indigo-600 hover:bg-indigo-700 transition-colors">
                Assinar VIP
              </button>
            </div>

          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-950 border-t border-slate-800 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">

            <div className="flex items-center gap-2">
              <Compass className="h-6 w-6 text-rose-500" />
              <span className="font-bold text-xl tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-rose-500 to-rose-400">
                HypeMap
              </span>
            </div>

            <div className="flex gap-6">
              <a href="#" className="text-slate-400 hover:text-white text-sm transition-colors">Termos de Uso</a>
              <a href="#" className="text-slate-400 hover:text-white text-sm transition-colors">Privacidade</a>
              <a href="#" className="text-slate-400 hover:text-white text-sm transition-colors">Contato</a>
            </div>

            <div className="text-slate-500 text-sm">
              &copy; {new Date().getFullYear()} HypeMap. Todos os direitos reservados.
            </div>

          </div>
        </div>
      </footer>

    </div>
  );
};

export default HypeMap;
