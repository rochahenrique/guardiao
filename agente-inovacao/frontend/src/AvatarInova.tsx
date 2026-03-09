interface AvatarInovaProps {
  tamanho?: 'sm' | 'md' | 'lg';
}

export function AvatarInova({ tamanho = 'md' }: AvatarInovaProps) {
  const tamanhos = {
    sm: { container: 'w-8 h-8' },
    md: { container: 'w-12 h-12' },
    lg: { container: 'w-24 h-24' },
  };

  const t = tamanhos[tamanho];

  return (
    <div className={`${t.container} rounded-full overflow-hidden flex-shrink-0`}>
      <svg
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        {/* Definições de gradientes */}
        <defs>
          {/* Fundo gradiente */}
          <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00A1E0" />
            <stop offset="100%" stopColor="#00D4AA" />
          </linearGradient>
          
          {/* Gradiente da lâmpada (vidro) */}
          <linearGradient id="bulbGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFF9E6" />
            <stop offset="50%" stopColor="#FFEB3B" />
            <stop offset="100%" stopColor="#FFC107" />
          </linearGradient>
          
          {/* Brilho interno */}
          <radialGradient id="glowGradient" cx="50%" cy="40%" r="50%">
            <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.9" />
            <stop offset="50%" stopColor="#FFEB3B" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#FFC107" stopOpacity="0.3" />
          </radialGradient>
          
          {/* Base metálica */}
          <linearGradient id="baseGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#78909C" />
            <stop offset="50%" stopColor="#B0BEC5" />
            <stop offset="100%" stopColor="#78909C" />
          </linearGradient>
        </defs>

        {/* Fundo circular */}
        <circle cx="50" cy="50" r="50" fill="url(#bgGradient)" />

        {/* Raios de luz */}
        <g opacity="0.6">
          <line x1="50" y1="8" x2="50" y2="16" stroke="#FFFFFF" strokeWidth="3" strokeLinecap="round" />
          <line x1="22" y1="22" x2="28" y2="28" stroke="#FFFFFF" strokeWidth="3" strokeLinecap="round" />
          <line x1="78" y1="22" x2="72" y2="28" stroke="#FFFFFF" strokeWidth="3" strokeLinecap="round" />
          <line x1="12" y1="45" x2="20" y2="45" stroke="#FFFFFF" strokeWidth="3" strokeLinecap="round" />
          <line x1="88" y1="45" x2="80" y2="45" stroke="#FFFFFF" strokeWidth="3" strokeLinecap="round" />
        </g>

        {/* Corpo da lâmpada (bulbo) */}
        <ellipse cx="50" cy="42" rx="24" ry="26" fill="url(#bulbGradient)" />
        
        {/* Brilho interno */}
        <ellipse cx="50" cy="38" rx="18" ry="20" fill="url(#glowGradient)" />
        
        {/* Reflexo de luz */}
        <ellipse cx="40" cy="32" rx="6" ry="8" fill="white" opacity="0.7" />

        {/* Parte inferior do bulbo (conexão) */}
        <path
          d="M35 62 Q35 68 38 70 L62 70 Q65 68 65 62 L65 58 Q58 64 50 64 Q42 64 35 58 Z"
          fill="url(#bulbGradient)"
        />

        {/* Base metálica - rosca */}
        <rect x="38" y="70" width="24" height="6" rx="1" fill="url(#baseGradient)" />
        <rect x="38" y="74" width="24" height="2" fill="#607D8B" />
        <rect x="38" y="78" width="24" height="6" rx="1" fill="url(#baseGradient)" />
        <rect x="38" y="82" width="24" height="2" fill="#607D8B" />
        
        {/* Ponta da base */}
        <path
          d="M42 86 L42 90 Q50 94 58 90 L58 86 Z"
          fill="url(#baseGradient)"
        />

        {/* Rosto fofo */}
        {/* Olhos */}
        <ellipse cx="42" cy="42" rx="4" ry="5" fill="#5D4037" />
        <ellipse cx="58" cy="42" rx="4" ry="5" fill="#5D4037" />
        
        {/* Brilho nos olhos */}
        <circle cx="43.5" cy="40" r="1.5" fill="white" />
        <circle cx="59.5" cy="40" r="1.5" fill="white" />
        
        {/* Bochecha rosada */}
        <ellipse cx="34" cy="50" rx="4" ry="2.5" fill="#FFAB91" opacity="0.6" />
        <ellipse cx="66" cy="50" rx="4" ry="2.5" fill="#FFAB91" opacity="0.6" />
        
        {/* Sorriso fofo */}
        <path
          d="M43 52 Q50 60 57 52"
          stroke="#5D4037"
          strokeWidth="2.5"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
    </div>
  );
}

export default AvatarInova;