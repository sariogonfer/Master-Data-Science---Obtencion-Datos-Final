# coding: utf-8

from copy import deepcopy
import argparse

from lxml import etree
import requests


arg_parse = argparse.ArgumentParser()
arg_parse.add_argument('--out-xml', dest='out_xml', action='store',
        default='out.xml')
arg_parse.add_argument('--out-rdf', dest='out_rdf', action='store',
        default='out.rdf')
arg_parse.add_argument('--no-store-partial-files', dest='store_partial_files',
                       action='store_false', help=('Si se activa, no se'
                       ' guardarán los ficheros XML utilizados durante el'
                       ' procesamiento.'))

APP_ID = 'add87c32'
APP_KEY = 'fbdce5cd55f060a547c6d7ad697ac71afbdce5cd55f060a547c6d7ad697ac71a'

ST_FACILITIES_URL = 'https://data.tfl.gov.uk/tfl/syndication/feeds/' \
        'stations-facilities.xml?app_id=%s&app_key=%s' % (APP_ID, APP_KEY)
ST_STATIONS_URL = 'https://tfl.gov.uk/tfl/syndication/feeds/' \
        'step-free-tube-guide.xml'

er_ns = {'er': 'ELRAD'}

def get_st_facilities_elem(parser):
    ''' Desgarga y parsea el fichero station-facilities.xml '''
    response = requests.get(ST_FACILITIES_URL)
    return etree.fromstring(response.content, parser)


def get_stations_elem(parser):
    ''' Descarga y parsea el fichero strep-free-tube-guide.xml '''
    response = requests.get(ST_STATIONS_URL)
    return etree.fromstring(response.content, parser)


def remove_elem_from_elem(elem, xpath, namespaces=None):
    ''' Filtra y elimina los nodos dentro de un elemento XML.

    Filtra los nodos utilizando el xpath pasado de dentro de un elemento XML y
    los elimina.

    Argumentos:
    elem -- Elemento del cual hay que eliminar los nodos.
    xpath -- xpath con el que se deben filtrar los nodos que se quiere
    eliminar
    namespaces -- Diccionario de namespaces al que pertenecen los elementos.
    Ejemplo: {'ns': 'ELRAD'}. Default: None
    '''

    [x.getparent().remove(x) for x in elem.xpath(xpath, namespaces=namespaces)]


def _clean_name(name):
    ''' Función auxiliar utilizada para normalizar nombres '''
    return name.replace("(", "").replace(")", "").replace("-", " ").replace(
        '\u2019', "'").lower()

def special_merge_elem(source_1, xpath_1, source_2, xpath_2, nms=None):
    ''' Función utilizada para unir dos elementos en uno.

    Función que recurre dos fuentes de elementos y une aquellos que coinciden
    en el contenido de los elementos indicados por los xparh respectivos.

    Argumentos:
    source_1 -- Fuente de elemenos principal y sobre la que se va a realizar
    la unión.
    xpath_1 -- xpath de elementos elemento comun utilizado para source_1
    source_2 -- Fuente de elementos secundaria.
    xpath_2 -- xpath de los elementos comun utilizado para source_2
    nms -- Diccionario de namespaces de los elementos en comun en caso de ser
    necesario.
    Ejemplo: {'ns': 'ELRAD'}. Default: None.
    '''

    res = deepcopy(source_1)
    src2 = deepcopy(source_2)
    for x in res.xpath(xpath_1, namespaces=nms):
        name_1 = _clean_name(x.text)
        for i in src2.xpath(xpath_2, namespaces=nms):
            name_2 = _clean_name(i.text)
            if name_1 == name_2:
                [x.getparent().append(j) for j in i.getparent().getchildren()
                 if j.tag != 'name']
                break
    return res

def get_xml():
    ''' Devuelve los XML procesados'''
    xml_parser = etree.XMLParser()
    facilities_elem = get_st_facilities_elem(xml_parser)
    stations_elem = get_stations_elem(xml_parser)
    remove_elem_from_elem(facilities_elem, '//openingHours')
    remove_elem_from_elem(stations_elem,
                          '//er:AccessibilityType[text()="None"]',
                          namespaces=er_ns)

    final = special_merge_elem(stations_elem, '//er:Station/er:StationName',
                               facilities_elem, '//station/name', nms=er_ns)
    return final, facilities_elem, stations_elem

def generate_xml(args):
    ''' Procesa los XML y los escribe, en caso de que se solicite, en ficheros
    de salida
    '''

    xml, facilities, stations = get_xml()

    with open(args.out_xml, 'wb') as out_1:
        et = etree.ElementTree(xml)
        et.write(out_1, pretty_print=True)

    if args.store_partial_files:
        with open('StationFacilitiesNOH.xml', 'wb') as out_2:
            et = etree.ElementTree(facilities)
            et.write(out_2, pretty_print=True)

        with open('StepFreeTubeNNone.xml', 'wb') as out_3:
            et = etree.ElementTree(stations)
            et.write(out_3, pretty_print=True)

        return [out_1.name, out_2.name, out_3.name]
    else:
        return [out_1.name]

if __name__ == '__main__':
    generate_xml(arg_parse.parse_args())
