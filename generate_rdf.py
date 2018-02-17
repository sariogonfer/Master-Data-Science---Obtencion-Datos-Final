from functools import partial
from hashlib import md5
import argparse
import re

from rdflib import BNode, Graph, Literal, URIRef, Namespace

from generate_xml import get_xml


arg_parse = argparse.ArgumentParser()
arg_parse.add_argument('--in-xml', dest='in_xml', action='store',
        default='')
arg_parse.add_argument('--out-rdf', dest='out_rdf', action='store',
        default='./out.rdf')

er = {'ns': 'ELRAD'}
tfl_ns = Namespace('http://tfl.gov.uk/tfl#')
schema_ns = Namespace('https://schema.org/')

graph = None


''' A continuación se definen funciones auxiliares que relizan ciertas acciones
comunes para el procesamiento de varios elementos del XML.
'''
def _clean_name(name):
    return name.replace("(", "").replace(")", "").replace("-", " ").replace(
        '\u2019', "'")

def _valid_uri_name(name):
    return name.replace(" ", "_")

def _valid_empty_name(name):
    return name.replace(" ", "")

def _text_as_literal(elem):
    """ Extrae de un elemento XML su texto y lo transforma a Literal

    Argumentos:
    elem -- elemento XML

    """
    if elem.text:
        return Literal(elem.text)
    return None

def _elem_to_has(elem, ns=tfl_ns, obj=Literal("yes")):
    aux = 'has' + re.sub('{.*}', '', elem.tag)
    obj_ = obj(elem) if callable(obj) else obj
    return getattr(ns, aux), obj_

def _attr_to_has(elem, attr_name, ns=tfl_ns, obj=Literal("yes")):
    for attr_ in elem.xpath('./@%s' % attr_name):
        aux = 'has' + _valid_empty_name(attr_)
        obj_ = obj(elem) if callable(obj) else obj
        return getattr(ns, aux), obj_
    return None

def add_triplet(elem, xpath, subj=None, pred=None, obj=_text_as_literal):
    """ Crea una tripleta utilizando los elementos de elem que filtra con XPATH

    Argumentos:
    elem -- Elemento XML del que extrae la informacion
    xpath -- XPATH utilizado para filtrar los elementos
    subj -- Sujeto de la tripleta. Puede ser una función o un objeto. En caso
        de ser una funcion, se llamara pasandole el elemento como parametro.
    pred -- Predicado de la tripleta. Puede ser una función o un objeto. En
        caso de ser una funcion, se llamara pasandole el elemento como
        parametro.
    obj -- Objeto de la tripleta. Puede ser una función o un objeto. En caso
        de ser una funcion, se llamara pasandole el elemento como parametro.
    """
    for aux in elem.xpath(xpath, namespaces=er):
        # Creamos los componentes de la tripleta según su tipo
        subj_ = subj(aux) if callable(subj) else subj
        pred_ = pred(aux) if callable(pred) else pred
        obj_ = obj(aux) if callable(obj) else obj
        # Comprueba si tiene un objeto valido que añadir
        if obj_:
            graph.add((subj_, pred_, obj_))

'''
A continuacion se definen funciones espècificas para cada elemetos del XML a
procesar
'''
def process_contact_details(st_elem, to_node):
    for i, contact_detail in enumerate(
            st_elem.xpath('./ns:contactDetails', namespaces=er)):
        contact_detail_node = BNode('#%sContactDetail%d' % (str(to_node), i))
        add_func = partial(add_triplet, contact_detail,
                           subj=contact_detail_node)
        add_func('./ns:address', pred=schema_ns.address)
        add_func('./ns:phone', pred=schema_ns.telephone)
        graph.add((to_node, tfl_ns.hasContactDetail, contact_detail_node, ))

def process_serving_lines(st_elem, to_node):
    for n_elem in st_elem.xpath('./ns:servingLines/ns:servingLine',
                                namespaces=er):
        line_name_ = n_elem.text
        n_node = BNode('Line%s' % _valid_uri_name(line_name_))
        graph.add((n_node, schema_ns.description, Literal(line_name_), ))
        graph.add((to_node, tfl_ns.servesLine, n_node, ))

def process_zones(st_elem, to_node):
    for n_elem in st_elem.xpath('./ns:zones/ns:zone', namespaces=er):
        zone_name_ = n_elem.text
        n_node = BNode('Zone%s' % _valid_uri_name(zone_name_))
        graph.add((n_node, schema_ns.description, Literal(zone_name_), ))
        graph.add((to_node, tfl_ns.belongsToZone, n_node, ))

def process_facilities(st_elem, to_node):
    for n_elem in st_elem.xpath('./ns:facilities/ns:facility', namespaces=er):
        graph.add((to_node, *_attr_to_has(n_elem, 'name',
                                          obj=_text_as_literal), ))

def process_placemark(st_elem, to_node):
    for i, placemark in enumerate(
            st_elem.xpath('./ns:Placemark', namespaces=er)):
        placemark_node = BNode('#%sPlacemark%d' % (str(to_node), i))
        add_func = partial(add_triplet, placemark, subj=placemark_node)
        add_func('./ns:name', pred=schema_ns.name)
        add_func('./ns:description', pred=schema_ns.description)
        add_func('./ns:Point/ns:coordinates', pred=tfl_ns.hasCoordinates)
        add_func('./ns:styleUrl', pred=tfl_ns.hasStyleUrl)
        graph.add((to_node, tfl_ns.hasPlacemark, placemark_node, ))

def process_lines(st_elem, to_node):
    for i, n_elem in enumerate(
            st_elem.xpath('./ns:Lines/ns:Line', namespaces=er)):
        name_ = n_elem.find('ns:LineName', namespaces=er).text
        platform_ = n_elem.find('ns:Platform', namespaces=er).text
        direction_ = n_elem.find('ns:Direction', namespaces=er).text
        direction_towards_ = n_elem.find('ns:DirectionTowards',
                                         namespaces=er).text
        step_min_ = n_elem.find('ns:StepMin', namespaces=er).text
        step_max_ = n_elem.find('ns:StepMax', namespaces=er).text
        gap_min_ = n_elem.find('ns:GapMin', namespaces=er).text
        gap_max_ = n_elem.find('ns:GapMax', namespaces=er).text
        manual_ramp_ = n_elem.find('ns:LevelAccessByManualRamp',
                                   namespaces=er).text
        location_lvl_access_ = n_elem.find('ns:LocationOfLevelAccess',
                                           namespaces=er).text

        line_node = BNode('#%sLineConnection%d' % (str(to_node), i))
        line_name_node = BNode('Line%s' % _valid_uri_name(name_))
        graph.add((line_name_node, tfl_ns.description, Literal(name_), ))
        graph.add((line_node, tfl_ns.lineDetail, line_name_node, ))
        graph.add((line_node, tfl_ns.platformNumber, Literal(platform_), ))
        graph.add((line_node, tfl_ns.direction, Literal(direction_), ))
        graph.add((line_node, tfl_ns.directionTowards,
                   Literal(direction_towards_), ))
        graph.add((line_node, tfl_ns.hasMinSteps, Literal(step_min_), ))
        graph.add((line_node, tfl_ns.hasMaxSteps, Literal(step_max_), ))
        graph.add((line_node, tfl_ns.hasMinGap, Literal(gap_min_), ))
        graph.add((line_node, tfl_ns.hasMaxGap, Literal(gap_max_), ))
        graph.add((line_node, tfl_ns.hasLevelAccessByManualRamp,
                   Literal(manual_ramp_), ))
        graph.add((line_node, tfl_ns.locationOfLevelAccess,
                   Literal(location_lvl_access_), ))
        graph.add((to_node, tfl_ns.hasLineConnection, line_node, ))

def process_toilets(st_elem, to_node):
    for i, toilet in enumerate(
            st_elem.xpath('./ns:PublicToilet', namespaces=er)):

        toilet_node = BNode('#%sToilet%d' % (str(to_node), i))
        add_func = partial(add_triplet, toilet, subj=toilet_node)
        add_func('./ns:Location', pred=schema_ns.location)
        add_func('./ns:PaymentRequired', pred=tfl_ns.paymentRequired)
        graph.add((to_node, tfl_ns.hasToilet, toilet_node, ))

def process_accesible_interchanges(st_elem, to_node):
    elem = st_elem.find('./ns:AccessibleInterchanges', namespaces=er)

    for i_elem in elem.xpath(
            "./*[substring(name(),string-length(name())-10) = 'Interchange']"):
        graph.add((to_node, *_elem_to_has(i_elem)))

def process_naptans(st_elem, to_node):
    for n_elem in st_elem.find('ns:Naptans', namespaces=er).xpath(
            './ns:Naptan', namespaces=er):
        id_ = n_elem.find('ns:NaptanID', namespaces=er).text
        desc = n_elem.find('ns:Description', namespaces=er).text
        n_node = BNode('naptan_%s' % id_)
        graph.add((n_node, schema_ns.description, Literal(desc), ))
        graph.add((to_node, tfl_ns.hasNaptan, n_node, ))

def process_accessibility(st_elem, to_node):
    for a_elem in st_elem.find('ns:Accessibility',
                               namespaces=er).getchildren():
        if not a_elem.text:
            continue
        graph.add((to_node, *_elem_to_has(a_elem, obj=_text_as_literal), ))

def process_entrance(en_elem, st_node):
    name = en_elem.find('ns:name', namespaces=er).text
    id_ = 'entrance_' + md5(name.encode()).hexdigest()
    en_node = BNode(getattr(tfl_ns, id_))
    add_func = partial(add_triplet, en_elem, subj=en_node)
    add_func('./ns:name', pred=schema_ns.name)
    add_func('./ns:entranceToBookingHall', pred=lambda e: _elem_to_has(e)[0])
    def _get_booking_hall_to_platform(bh2p_elem):
        bh2p_node = BNode()
        bh2p_add_func = partial(add_triplet, bh2p_elem, subj=bh2p_node)
        bh2p_add_func('ns:pointName', pred=tfl_ns.pointName)
        bh2p_add_func('ns:pathDescription', pred=tfl_ns.pathDescription)
        for i, path in enumerate(bh2p_elem.xpath('./ns:path', namespaces=er)):
            p_node = BNode(id_ + 'PATH_%d' % i)
            p_add_func = partial(add_triplet, path, subj=p_node)
            p_add_func('./ns:heading', pred=tfl_ns.heading)
            p_add_func('./ns:pathDescription', pred=tfl_ns.pathDescription)
            graph.add((bh2p_node, tfl_ns.path, p_node, ))

        return bh2p_node
    def _get_platform_to_train(p2t_elem):
        p2t_node = BNode()
        p2t_add_func = partial(add_triplet, p2t_elem, subj=p2t_node)
        def _get_train(train_elem):
            try:
                train_name = train_elem.find('ns:trainName',
                                             namespaces=er).text
            except:
                return None
            train_node = BNode('train_' + train_name)
            graph.add((train_node, schema_ns.name, Literal(train_name), ))

            return train_node

        p2t_add_func('ns:trainName', pred=tfl_ns.train, obj=_get_train)
        p2t_add_func('ns:platformToTrainSteps', pred=tfl_ns.steps)

        return p2t_node

    add_func('ns:bookingHallToPlatform', pred=tfl_ns.hasBookingHallToPlatform,
             obj=_get_booking_hall_to_platform)
    add_func('ns:platformToTrain', pred=tfl_ns.hasPlatformToTrain,
             obj=_get_platform_to_train)
    graph.add((st_node, tfl_ns.hasEntrance, en_node, ))

def process_entrances(st_elem, to_node):
    try:
        entrances = st_elem.find('ns:entrances', namespaces=er).xpath(
            'ns:entrance', namespaces=er)
    except:
        return None
    for en_elem in entrances:
        process_entrance(en_elem, to_node)


def get_rdf_graph(xml_source):
    global graph
    graph = Graph()

    for st_elem in xml_source.xpath('//ns:Station', namespaces=er):
        st_name = _clean_name(st_elem.find('./ns:StationName',
                                           namespaces=er).text)
        uri_name = _valid_uri_name(st_name)
        st_node = getattr(tfl_ns, uri_name)
        graph.add((st_node, schema_ns.name, Literal(st_name)))
        process_toilets(st_elem, st_node)
        process_contact_details(st_elem, st_node)
        process_serving_lines(st_elem, st_node)
        process_zones(st_elem ,st_node)
        process_facilities(st_elem, st_node)
        process_placemark(st_elem, st_node)
        process_lines(st_elem, st_node)
        process_accesible_interchanges(st_elem, st_node)
        process_naptans(st_elem, st_node)
        process_accessibility(st_elem, st_node)
        process_entrances(st_elem, st_node)

    return graph


def generate_rdf(args):
    if not getattr(args, 'in_xml', ''):
        xml = get_xml()
    else:
        from lxml import etree
        xml = etree.parse(getattr(args, 'in_xml'))
    get_rdf_graph(xml)
    graph.serialize(destination=args.out_rdf, format="xml")

    return [args.out_rdf]

if __name__ == '__main__':
    print('Se ha generado el fichero RDF en %s' %
          generate_rdf(arg_parse.parse_args()))
