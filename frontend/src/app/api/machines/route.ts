import { NextResponse } from "next/server";
import { GoogleSpreadsheet } from "google-spreadsheet";
import { JWT } from "google-auth-library";
import * as fs from "fs";
import * as path from "path";

// Força a rota a ser dinâmica (sempre buscar do sheets em tempo real)
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const spreadsheetId = process.env.SPREADSHEET_ID;
    
    if (!spreadsheetId) {
      return NextResponse.json(
        { error: "SPREADSHEET_ID ausente no .env" },
        { status: 500 }
      );
    }

    let clientEmail = process.env.GOOGLE_CLIENT_EMAIL;
    // Em alguns ambientes o newline \n pode vir escapado como \\n
    let privateKey = process.env.GOOGLE_PRIVATE_KEY?.replace(/\\n/g, "\n");

    // Fallback: se não estiver na nuvem, tenta ler do arquivo físico
    if (!clientEmail || !privateKey) {
      const credsPathEnv = process.env.GOOGLE_APPLICATION_CREDENTIALS;
      if (!credsPathEnv) {
        return NextResponse.json(
          { error: "Credenciais de nuvem ausentes e GOOGLE_APPLICATION_CREDENTIALS não definido." },
          { status: 500 }
        );
      }
      
      const credsPath = path.resolve(process.cwd(), credsPathEnv);
      if (!fs.existsSync(credsPath)) {
        return NextResponse.json(
          { error: `Arquivo de credenciais não encontrado em: ${credsPath}` },
          { status: 500 }
        );
      }

      const credsRaw = fs.readFileSync(credsPath, "utf-8");
      const creds = JSON.parse(credsRaw);
      clientEmail = creds.client_email;
      privateKey = creds.private_key;
    }

    const jwt = new JWT({
      email: clientEmail,
      key: privateKey,
      scopes: ["https://www.googleapis.com/auth/spreadsheets.readonly"],
    });

    const doc = new GoogleSpreadsheet(spreadsheetId, jwt);
    await doc.loadInfo(); 

    const sheet = doc.sheetsByIndex[0];
    const rows = await sheet.getRows();

    const machines = rows.map((row, index) => {
      return {
        id: index,
        marca: row.get("Marca") || "",
        modelo: row.get("Modelo") || "",
        ano: row.get("Ano de Fabricação") || "",
        horasMotor: row.get("Horas de Motor") || "",
        horasRotor: row.get("Horas de Rotor") || "",
        tipoPlataforma: row.get("Tipo Plataforma") || "",
        preco: row.get("Preço") || "",
        localizacao: row.get("Localização") || "",
        url: row.get("URL Anúncio") || "",
        categoria: row.get("Categoria") || "",
      };
    });

    return NextResponse.json({ machines });
  } catch (error: any) {
    console.error("Erro na API /api/machines:", error);
    return NextResponse.json(
      { error: "Falha ao ler dados", details: error.message },
      { status: 500 }
    );
  }
}
