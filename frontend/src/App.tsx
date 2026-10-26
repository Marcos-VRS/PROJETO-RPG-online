import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { ensureCsrf, fetchMe } from "./lib/api";

const DJANGO_LOGIN_URL = "http://localhost:8000/accounts/login/?next=/admin/";

export default function App() {
  useEffect(() => {
    ensureCsrf().catch(() => {
      /* primeira chamada pode falhar se backend ainda subindo; ignora */
    });
  }, []);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["me"],
    queryFn: fetchMe,
  });

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-stone-400">
        Carregando...
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
        <h1 className="text-3xl font-bold text-stone-100">Roll3d6</h1>
        <p className="text-stone-400">Você não está autenticado.</p>
        <a
          className="rounded-md bg-amber-600 px-4 py-2 font-semibold text-stone-950 hover:bg-amber-500"
          href={DJANGO_LOGIN_URL}
        >
          Entrar
        </a>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 p-8 text-center">
      <h1 className="text-3xl font-bold text-stone-100">Roll3d6</h1>
      <p className="text-stone-300">
        Olá, <span className="font-semibold text-amber-400">{data.username}</span>!
      </p>
      <p className="text-sm text-stone-500">
        Lobby e mesas chegam na F-4. Por enquanto, autenticação ponta-a-ponta funcionando.
      </p>
    </div>
  );
}
