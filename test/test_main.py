import main


def test_pdf_invalido_no_registra_candidato(monkeypatch):
    llamado = False

    def no_deberia_guardar(*args, **kwargs):
        nonlocal llamado
        llamado = True

    def pdf_inexistente(*args, **kwargs):
        raise FileNotFoundError("No existe un PDF válido")

    monkeypatch.setattr(main, "extraer_texto_por_pagina", pdf_inexistente)
    monkeypatch.setattr(main, "guardar_candidato", no_deberia_guardar)

    try:
        main.correr_flujo("inexistente.pdf", "cand", "Candidata")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Debía informar que el PDF no existe")
    assert not llamado


def test_descarga_plan_cne_y_devuelve_ruta_del_manifiesto(monkeypatch):
    candidatura = type("Candidatura", (), {"id": "cand-cne"})()

    class _Scraper:
        def descubrir_candidaturas(self, proceso_id):
            assert proceso_id == "seccionales_2023"
            return [candidatura]

        def descargar_planes(self, proceso_id, candidaturas):
            assert candidaturas == [candidatura]
            return {"documentos": [{"id": "cand-cne", "archivo_local": "data/raw/seccionales_2023/cand-cne.pdf"}]}

    monkeypatch.setattr(main, "ScraperCNE", _Scraper)
    ruta, resultado = main.descargar_plan_cne("seccionales_2023", "cand-cne")

    assert ruta == "data\\raw\\seccionales_2023\\cand-cne.pdf"
    assert resultado is candidatura
