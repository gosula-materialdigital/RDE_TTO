"""
Maps the RDE-structured tensile-test metadata (meta/{process_id}_metadata.json)
onto Tensile Test Ontology / PMD Core Ontology classes, producing a
canonical JSON graph.

Field-level blocks are driven by metadata-def.json (class name, unit,
sdc type, denotes, ...); the testing process, test piece and equipment
scaffolding is fixed domain knowledge and stays explicit below.
"""
import json
import re
from datetime import datetime
from pathlib import Path



def create_quality_blocks(process_id, key, quality_class, value, unit_id, is_about, quality_type, process):
    """
    Returns a list of blocks representing the semantic chain for a single quality.
    """
    measurement_id = f"{process_id}_{key.lower().replace(' ', '')}"
    
    # 1. Create the base value specification dictionary
    value_spec = {
        "hasIdentifier": f"{measurement_id}_valuespecification",
        "label": f"{measurement_id}_valuespecification",
        "has measurement unit label": [{
            "Measurement Unit Label": {
                "hasIdentifier": unit_id,
                "label": unit_id
            }
        }],
        "specifies value of": [{ quality_class: { "hasIdentifier": measurement_id , "label": measurement_id }}]
    }

    if key == 'temperature':
       value_spec["has specified numeric value"]= float(23.0)
    else:
        value_spec["has specified numeric value"]= float(value)


    datum_block = {
        "Measurement Datum": {
            "hasIdentifier": f"{measurement_id}_measurement_datum",
            "label": f"{measurement_id}_measurement_datum",
            "is quality measurement of": [{ quality_class: { "hasIdentifier": measurement_id , 'label': measurement_id} }],
            "has value specification": [{
                "Scalar Value Specification": value_spec
            }]
        }
    }

    if process is not None:
        datum_block["Measurement Datum"]["is specified output of"] = [{
            process: {
                "hasIdentifier": f"{process_id}_{process.lower().replace(' ', '')}"
            }}]
        
    quality_block = {
        quality_class: {
            "hasIdentifier": measurement_id,
            "label": measurement_id,
        }
    }
        
    if is_about == 'Object':
        if quality_type is not None:
            quality_block[quality_class][quality_type] = [{
                is_about: {
                    "hasIdentifier": f"{process_id}_air"
                }}]

    else:
        if quality_type is not None:
            quality_block[quality_class][quality_type] = [{
                is_about: {
                    "hasIdentifier": f"{process_id}_{is_about.lower().replace(' ', '')}"

                    }}] 
            
    if quality_type== 'characteristic of':    
        quality_block[quality_class]["realized in"] = [{
            process: {
                "hasIdentifier":  f"{process_id}_{process.lower().replace(' ', '')}"
            }}]

    elif quality_type== None:
        None
    
    else:
        quality_block[quality_class]["characteristic measured by assay"] = [{
            process: {
                "hasIdentifier":  f"{process_id}_{process.lower().replace(' ', '')}"
            }}]
       
    return [quality_block, datum_block]

def create_identifier_and_value_blocks(class_name, key, process_id, value, denotes, denotes_instance_name):
    """
    Returns a list of blocks representing the semantic chain for identifiers and values.
    """
   
    if key == 'materialspecimenshape':
        datum_block = {
            class_name: {
                "hasIdentifier": f"{process_id}_{key}",
                "label": f"{process_id}_{key}",
                "has part": [
                    {
                    "Specification Datum": {
                        "hasIdentifier": f"{process_id}_{key}_original_thickness",
                        "label": f"{process_id}_{key}_original_thickness",
                        "is subject of": [
                            {
                            "Original Thickness": {
                                "hasIdentifier":f"{process_id}_a1",
                            }},
                            {
                            "Original Thickness": {
                                "hasIdentifier":f"{process_id}_a2",
                            }},
                            {
                            "Original Thickness": {
                                "hasIdentifier":f"{process_id}_a3",
                            }}
                            ],
                        "specified by value": [{
                            "Scalar Value Specification": {
                                "hasIdentifier": f"{process_id}_{key}_original_thickness_valuespecification",
                                "label": f"{process_id}_{key}_original_thickness_valuespecification",
                                "has specified numeric value": float(re.findall(r'\d+', str(value))[0]),
                                "has measurement unit label": [{
                                    "Measurement Unit Label": {
                                        "hasIdentifier": "unit:MilliM",
                                        "label": "unit:MilliM"
                                    }}],}}]}},

                    {
                    "Specification Datum": {
                        "hasIdentifier": f"{process_id}_{key}_original_width",
                        "label": f"{process_id}_{key}_original_width",
                        "is subject of": [
                            {
                            "Original Width": {
                                "hasIdentifier":f"{process_id}_b1",
                            }},
                            {
                            "Original Width": {
                                "hasIdentifier":f"{process_id}_b2",
                            }},
                            {
                            "Original Width": {
                                "hasIdentifier":f"{process_id}_b3",
                            }}
                            ],
                        "specified by value": [{
                            "Scalar Value Specification": {
                                "hasIdentifier": f"{process_id}_{key}_original_width_valuespecification",
                                "label": f"{process_id}_{key}_original_width_valuespecification",
                                "has specified numeric value": float(re.findall(r'\d+', str(value))[1]),
                                "has measurement unit label": [{
                                    "Measurement Unit Label": {
                                        "hasIdentifier": "unit:MilliM",
                                        "label": "unit:MilliM"
                                    }}],}}]}},

                    {
                    "Specification Datum": {
                        "hasIdentifier": f"{process_id}_{key}_original_guagelength",
                        "label": f"{process_id}_{key}_original_guagelength",
                        "is subject of": [
                            {
                            "Original Gauge Length": {
                                "hasIdentifier":f"{process_id}_L0",
                                "label":f"{process_id}_L0",
                            }}
                            ],
                        "specified by value": [{
                            "Scalar Value Specification": {
                                "hasIdentifier": f"{process_id}_{key}_original_guagelength_valuespecification",
                                "label": f"{process_id}_{key}_original_guagelength_valuespecification",
                                "has specified numeric value": float(re.findall(r'\d+', str(value))[2]),
                                "has measurement unit label": [{
                                    "Measurement Unit Label": {
                                        "hasIdentifier": "unit:MilliM",
                                        "label": "unit:MilliM"
                                    }}],}}]}},
                ]
            }}

    elif class_name == 'Device Specification' or class_name == 'Material Specification':          
        identifier = {
            "hasidentifier": f"{process_id}_{key}_identifier", 
            "label": f"{process_id}_{key}_identifier", 
        }

        if value == 'DIN EN ISO 17025':
            identifier["has url"]= "https://www.dinmedia.de/de/norm/din-en-iso-iec-17025/278030106"
        
        elif value == "DIN EN ISO 6892-1":
            identifier["has url"]= "https://www.dinmedia.de/de/norm/din-en-iso-6892-1/317931281"
        
        elif value == "DIN EN ISO 7500-1:2018, DIN EN ISO 9513":
            identifier["has url"]= ["https://www.dinmedia.de/en/standard/din-en-iso-7500-1/288322423", "https://www.dinmedia.de/en/standard/din-en-iso-9513/155624639"]
        else:
            identifier["has value"]= value

        datum_block = {
            class_name: {
                "hasIdentifier": f"{process_id}_{key}",
                "label": f"{process_id}_{key}",
                "denoted by": [{
                    "Identifier": identifier
                }]
            }}

    else:         
        datum_block = {
            class_name: {
                "hasIdentifier": f"{process_id}_{key}",
                "label": f"{process_id}_{key}",
                "has value": value
            }}
        
        if denotes is not None:
            datum_block[class_name]["denotes"] = [{
                denotes:{
                    "hasIdentifier": f"{process_id}_{denotes_instance_name}",
                    "label": f"{process_id}_{denotes_instance_name}"
                        }}]

    return [datum_block]


def transform_json_to_canonical(metadata_json_path, metadata_def_json_path, output_json_path):
    canonical_list = []
    with open(metadata_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(metadata_def_json_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    process_id = data['constant']['process_id']['value']
    for column_name, info in data['constant'].items():
        value = info['value']
        unit = info.get('unit', '')         
        if column_name in metadata:
            metadata_block = metadata[column_name]
            if "class name" in metadata_block:
                if "unit" in metadata_block:
                    if "independent continuant" in metadata_block:
                        is_about = metadata_block["independent continuant"]
                        quality_type = metadata_block["sdc type"]
                        process = metadata_block["process"]
                    else:
                        is_about = None
                        quality_type = None
                        process = None
                    block = create_quality_blocks(process_id, metadata_block["instance name"], metadata_block["class name"], value, unit, is_about, quality_type, process)
                    canonical_list.extend(block)
                else:
                    if "denotes" in metadata_block:
                        denotes = metadata_block["denotes"]
                    else:
                        denotes = None
                    if "denotes instance name" in metadata_block:
                        denotes_instance_name = metadata_block["denotes instance name"]
                    else:
                        denotes_instance_name = None

                    blocks = create_identifier_and_value_blocks(metadata_block["class name"], metadata_block["instance name"], process_id, value, denotes, denotes_instance_name)
                    canonical_list.extend(blocks)
        

    process_block = {
        "Tensile Testing Process": {
            "hasIdentifier": f"{process_id}_tensiletestingprocess",
            "label": f"{process_id}_tensiletestingprocess",
            "has participant": [{ "Tensile Testing Machine": { "hasIdentifier": f"{process_id}_tensiletestingmachine", "label": f"{process_id}_tensiletestingmachine"} },
                                { "Extensometer": { "hasIdentifier": f"{process_id}_extensometer", "label": f"{process_id}_extensometer"} },
                                { "Micrometer Gauge": { "hasIdentifier": f"{process_id}_micrometergauge", "label": f"{process_id}_micrometergauge"} },
                                { "Caliper": { "hasIdentifier": f"{process_id}_caliper", "label": f"{process_id}_caliper"} },
                                { "Load Cell": { "hasIdentifier": f"{process_id}_loadcell", "label": f"{process_id}_loadcell" }},
                                { "Organization": { "hasIdentifier": f"{process_id}_organization", "label": f"{process_id}_organization" }},
                                { "Homo Sapiens": { "hasIdentifier": f"{process_id}_homosapiens", "label": f"{process_id}_homosapiens"}},
                                { "Object": { "hasIdentifier": f"{process_id}_air", "label": f"{process_id}_air"}}],
            "has specified input": [{ "Tensile Testpiece": { "hasIdentifier": f"{process_id}_tensiletestpiece", "label": f"{process_id}_tensiletestpiece"}}],
            "realizes": [{ "Test Piece Role": { "hasIdentifier": f"{process_id}_testpiecerole"}},
                         { "Broken Tested Test Piece Role": { "hasIdentifier": f"{process_id}_testpiece_1_aftertest_role"}},
                         { "Broken Tested Test Piece Role": { "hasIdentifier": f"{process_id}_testpiece_2_aftertest_role"}},
                         { "Role": { "hasIdentifier": f"{process_id}_operator_role", "label": f"{process_id}_operator_role", "role of":[{"Homo Sapiens": {"hasIdentifier": f"{process_id}_homosapiens", "label": f"{process_id}_homosapiens"}}]}},
                         { "Plan": { "hasIdentifier": f"{process_id}_tensiletestplan", "label": f"{process_id}_tensiletestplan"}},
                         ],
            "has process attribute": [{"Strain Rate": {"hasIdentifier": f"{process_id}_strainrate", "label": f"{process_id}_strainrate"}},
                                      {"Crosshead Separation Rate": {"hasIdentifier": f"{process_id}_crossheadseparationrate", "label": f"{process_id}_crossheadseparationrate"}},
                                      {"Transition Point": {"hasIdentifier": f"{process_id}_transitionpoint", "label": f"{process_id}_transitionpoint"}}],
            "exists at": [{"Temporal Region": {"hasIdentifier": f"{process_id}_temporalregion", "label": f"{process_id}_temporalregion"}}],
            "has specified output": [{ "Object": { "hasIdentifier": f"{process_id}_ouput_object_1", "label": f"{process_id}_ouput_object_1"}},
                                     { "Object": { "hasIdentifier": f"{process_id}_ouput_object_2", "label": f"{process_id}_ouput_object_2"}},
                                     {"Tensile Test Result": {"hasIdentifier": f"{process_id}_tensiletestresult", "label": f"{process_id}_tensiletestresult"}}],
    
        }
    }

    note = data['constant'].get('note', {}).get('value')
    if note:
        process_block["Tensile Testing Process"]["description"] = note
    
    canonical_list.append(process_block)
    canonical_list.append({
        "Plan": {
            "hasIdentifier": f"{process_id}_tensiletestplan", 
            "label": f"{process_id}_tensiletestplan",
            "concretizes": [{
                "Tensile Test Method": {
                    "hasIdentifier": f"{process_id}_tensiletestmethod", 
                    "label": f"{process_id}_tensiletestmethod",
                    "denoted by": [{
                        "Identifier": {
                            "hasIdentifier": f"{process_id}_tensiletestmethod_standard",
                            "label": f"{process_id}_tensiletestmethod_standard"
                        }
                    }]}

            }]
        }
    })

    date = data['constant'].get('date', {}).get('value')
    if date:
        canonical_list.append({
            "Temporal Region": {
            "hasIdentifier": f"{process_id}_temporalregion", 
            "label": f"{process_id}_temporalregion",
            "has first instant": [{
                "Temporal Instant": {
                    "hasIdentifier": f"{process_id}_temporalinterval_start", 
                    "label": f"{process_id}_temporalinterval_start",                 
                    "inXSDDateTimeStamp": f"{datetime.fromisoformat(str(date)):%Y-%m-%d}T00:00:00+02:00^^xsd:dateTime"
                }
                }],
            "has last instant": [{
                "Temporal Instant": {
                    "hasIdentifier": f"{process_id}_temporalinterval_end", 
                    "label": f"{process_id}_temporalinterval_end",
                    "inXSDDateTimeStamp": f"{datetime.fromisoformat(str(date)):%Y-%m-%d}T23:59:59+02:00^^xsd:dateTime"
                }
                }]
            }
        })

    canonical_list.append({
        "Tensile Testpiece": {
            "hasIdentifier": f"{process_id}_tensiletestpiece", 
            "label": f"{process_id}_tensiletestpiece",
            "has role": [{
                        "Test Piece Role": {
                            "hasIdentifier": f"{process_id}_testpiecerole",
                            "label": f"{process_id}_testpiecerole",
                        }}],
            "derives from": [{
                "Steel": {
                    "hasIdentifier": f"{process_id}_steel",
                    "label": f"{process_id}_steel",
                    "complies with": [{
                        "Material Specification":{
                            "hasIdentifier": f"{process_id}_materialdescription",
                            "label": f"{process_id}_materialdescription"}}]
                    }}],
            "complies with": [
                {"Material Specification":{"hasIdentifier": f"{process_id}_tensiletestpiece_type", "label": f"{process_id}_tensiletestpiece_type"}},
                {"Material Specification":{"hasIdentifier": f"{process_id}_tensiletestpiece_rollingdirection", "label": f"{process_id}_tensiletestpiece_rollingdirection"}},
                {"Material Specification":{"hasIdentifier": f"{process_id}_tensiletestpiece_shape", "label": f"{process_id}_tensiletestpiece_shape"}},
                ]}})
    
    canonical_list.append({
        "Object": {
            "hasIdentifier": f"{process_id}_ouput_object_1",
            "label": f"{process_id}_ouput_object_1",
            "has role": [{
                        "Broken Tested Test Piece Role": {
                            "hasIdentifier": f"{process_id}_testpiece_1_aftertest_role",
                            "label": f"{process_id}_testpiece_1_aftertest_role",
                        }}]}})      
 
    canonical_list.append({
        "Object": {
            "hasIdentifier": f"{process_id}_ouput_object_2",
            "label": f"{process_id}_ouput_object_2",
            "has role": [{
                        "Broken Tested Test Piece Role": {
                            "hasIdentifier": f"{process_id}_testpiece_2_aftertest_role",
                            "label": f"{process_id}_testpiece_2_aftertest_role",
                        }}]}})      

    canonical_list.append({
        "Tensile Testing Machine": { 
            "hasIdentifier": f"{process_id}_tensiletestingmachine", 
            "label": f"{process_id}_tensiletestingmachine",
            "complies with": [
                {
                "Device Specification":{
                    "hasIdentifier": f"{process_id}_tensiletestmachine_standard",
                    "label": f"{process_id}_tensiletestmachine_standard"}},
                {
                "Device Specification":{
                    "hasIdentifier": f"{process_id}_tensiletestmachine_type",
                    "label": f"{process_id}_tensiletestmachine_type"
                }}],

            "is_manufactured_by": [{
                "Manufacturer": {
                    "hasIdentifier": f"{process_id}_tensiletestmachine_manufacturer",
                    "label": f"{process_id}_tensiletestmachine_manufacturer"
                }}]
                }})

    canonical_list.append({
        "Extensometer": { 
            "hasIdentifier": f"{process_id}_extensometer", 
            "label": f"{process_id}_extensometer",
            "complies with": [{
                "Device Specification":{
                    "hasIdentifier": f"{process_id}_extensometer_standard",
                    "label": f"{process_id}_extensometer_standard"}}]
                }})
    
    canonical_list.append({
        "Caliper": { 
            "hasIdentifier": f"{process_id}_caliper", 
            "label": f"{process_id}_caliper",
            "is_manufactured_by": [{
                "Manufacturer": {
                    "hasIdentifier": f"{process_id}_calipermanufacturer",
                    "label": f"{process_id}_calipermanufacturer",
                }}]
                }})
    canonical_list.append({
        "Micrometer Gauge": { 
            "hasIdentifier": f"{process_id}_micrometergauge", 
            "label": f"{process_id}_micrometergauge",
            "is_manufactured_by": [{
                "Manufacturer": {
                    "hasIdentifier": f"{process_id}_micrometergaugemanufacturer",
                    "label": f"{process_id}_micrometergaugemanufacturer"
                }}]
                }})    
    canonical_list.append({
        "Load Cell": { 
            "hasIdentifier": f"{process_id}_loadcell", 
            "label": f"{process_id}_loadcell",}})

    canonical_list.append({
        "Organization": { 
            "hasIdentifier": f"{process_id}_organization", 
            "label": f"{process_id}_organization",
            "located in": [{
                "Site": {
                    "hasIdentifier": f"{process_id}_organization_site",
                    "label": f"{process_id}_organization_site",  
                }}]}})

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(canonical_list, f, indent=4, ensure_ascii=False)



if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parents[1] / "data"
    transform_json_to_canonical(
        data_dir / "meta" / "46NT9B_metadata.json",
        data_dir / "tasksupport" / "metadata-def.json",
        data_dir / "structured" / "canonical_json_file.json"
    )
