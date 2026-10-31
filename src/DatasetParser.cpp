#include "DatasetParser.hpp"
#include <iostream>
#include <pugixml.hpp>

vector<Vaga> DatasetParser::carregarVagasXML(const string& caminhoXML) {
    vector<Vaga> vagas;
    pugi::xml_document doc;

    pugi::xml_parse_result resultado = doc.load_file(caminhoXML.c_str());
    if (!resultado) {
        cerr << "[ERRO] Nao foi possivel carregar o XML: " << caminhoXML << endl;
        cerr << "Descricao do erro: " << resultado.description() << endl;
        return vagas;
    }

    pugi::xml_node parkingNode = doc.child("parking");
    for (pugi::xml_node spaceNode = parkingNode.child("space"); spaceNode; spaceNode = spaceNode.next_sibling("space")) {
        Vaga v;
        v.id = spaceNode.attribute("id").as_int();
        v.ocupadaReal = (spaceNode.attribute("occupied").as_int() == 1);

        pugi::xml_node contourNode = spaceNode.child("contour");
        for (pugi::xml_node pointNode = contourNode.child("point"); pointNode; pointNode = pointNode.next_sibling("point")) {
            int x = pointNode.attribute("x").as_int();
            int y = pointNode.attribute("y").as_int();
            v.contorno.push_back(Point(x, y));
        }

        // Calcula a Bounding Box manualmente (sem precisar da função boundingRect)
        if (!v.contorno.empty()) {
            int minX = v.contorno[0].x;
            int maxX = v.contorno[0].x;
            int minY = v.contorno[0].y;
            int maxY = v.contorno[0].y;

            for (const auto& p : v.contorno) {
                if (p.x < minX) minX = p.x;
                if (p.x > maxX) maxX = p.x;
                if (p.y < minY) minY = p.y;
                if (p.y > maxY) maxY = p.y;
            }

            v.caixaDelimitadora = Rect(minX, minY, maxX - minX, maxY - minY);
        }

        vagas.push_back(v);
    }

    return vagas;
}