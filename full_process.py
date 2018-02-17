''' Script que genera el fichero .xml y .rdd, ademas de los intermedios en
caso de ser necesarios, solicitados en la practica.

Parametros:
    --out-xml PATH -- Fichero xml de salida. Default: final.xml
    --out-rdf PATH -- Fichero rdf de salida. Default: final.rdf
    --no-store-partial-files -- Si se activa, no se guardarán los ficheros XML
    utilizados durante el procesamiento.
'''

from collections import namedtuple
import argparse
import sys

from generate_xml import generate_xml
from generate_rdf import generate_rdf

arg_parse = argparse.ArgumentParser(
    description=('Script que genera el fichero .xml y .rdd, ademas de los'
        ' intermedios en caso de ser necesarios, solicitados en la practica.'),
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
arg_parse.add_argument('--out-xml', dest='out_xml', action='store',
                       default='final.xml', help='Fichero xml de salida.')
arg_parse.add_argument('--out-rdf', dest='out_rdf', action='store',
                       default='final.rdf', help='Fichero rdf de salida.')
arg_parse.add_argument('--no-store-partial-files', dest='store_partial_files',
                       action='store_false', help=('Si se activa, no se'
                       ' guardarán los ficheros XML utilizados durante el'
                       ' procesamiento.'))


if __name__ == '__main__':
    args = arg_parse.parse_args()
    xml_path = generate_xml(args)
    args.in_xml = xml_path[0]
    rdf_path = generate_rdf(args)

    total_files = xml_path + rdf_path

    print('Se han generado los ficheros: ')
    print('- ' + '\n- '.join(total_files))
