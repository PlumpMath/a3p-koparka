#version 150

struct p3d_LightSourceParameters {
  // Primary light color.
  vec4 color;
 
  // Light color broken up into components, for compatibility with legacy shaders.
  vec4 ambient;
  vec4 diffuse;
  vec4 specular;
 
  // View-space position.  If w=0, this is a directional light, with
  // the xyz being -direction.
  vec4 position;
 
  // Spotlight-only settings
  vec3 spotDirection;
  float spotExponent;
  float spotCutoff;
  float spotCosCutoff;
 
  // Individual attenuation constants
  float constantAttenuation;
  float linearAttenuation;
  float quadraticAttenuation;
 
  // constant, linear, quadratic attenuation in one vector
  vec3 attenuation;
 
  // Shadow map for this light source
  sampler2DShadow shadowMap;
 
  // Transforms vertex coordinates to shadow map coordinates
  mat4 shadowMatrix;
}; 

uniform p3d_LightSourceParameters shadow_caster; 

uniform vec4 light_color[100];
uniform vec4 light_pos[100];
uniform vec4 light_att[100];
uniform int num_lights;
uniform vec3 camera_pos;
uniform vec3 ambient;
uniform vec3 light_vec;
uniform vec3 light_vec_color;
uniform sampler2D height_map;
uniform sampler2D tex0;
uniform sampler2D tex1;
uniform sampler2D tex2;
uniform sampler2D tex3;
uniform sampler2D tex4;
uniform sampler2D tex5;
uniform sampler2D tex0n;
uniform sampler2D tex1n;
uniform sampler2D tex2n;
uniform sampler2D tex3n;
uniform sampler2D tex4n;
uniform sampler2D tex5n;
uniform sampler2D atr1; // rgb vaules are for mapping details
uniform sampler2D atr2; // rgb vaules are for mapping details

in vec2 terrain_uv;
in vec4 world_pos;
in vec2 detail_uv;
in vec4 shadow_uv;

out vec4 final_color;


float PCF(sampler2DShadow depth_map, vec4 uv, float bias)
    {
    float result = 0.0;
    vec4 size=vec4(textureSize(depth_map, 0).xy, 1.0, 1.0);
    for(int x=-2; x<=2; x++)
        {
        for(int y=-2; y<=2; y++)
            {
            vec4 off = vec4(x,y, 0.0, 0.0)/size;
            result += textureProj(depth_map, uv+off, bias);
            }
        }
    return result/25.0;
    }


void main()
    {
    vec3 N=normalize(texture(height_map,terrain_uv).xyz*2.0-1.0);
    vec3 Left=vec3(1.0,0.0,0.0);
    vec3 V = normalize(world_pos.xyz - camera_pos); 
    vec3 color=vec3(0.0, 0.0, 0.0);
    float specular =0.0; 
    float gloss=0.0;
    
    //mix the textures
    vec4 mask1=texture2D(atr1,terrain_uv);
    vec4 mask2=texture2D(atr2,terrain_uv);
    //detail               
    vec3 detail = vec3(0.0,0.0,0.0);
        detail+=texture(tex0, detail_uv).rgb*mask1.r;
        detail+=texture(tex1, detail_uv).rgb*mask1.g;
        detail+=texture(tex2, detail_uv).rgb*mask1.b;
        detail+=texture(tex3, detail_uv).rgb*mask2.r;
        detail+=texture(tex4, detail_uv).rgb*mask2.g;
        detail+=texture(tex5, detail_uv).rgb*mask2.b;
    //normal 
    vec4 norm_map = vec4(0.0,0.0,0.0,0.0);
        norm_map+=texture(tex0n, detail_uv)*mask1.r;
        norm_map+=texture(tex1n, detail_uv)*mask1.g;
        norm_map+=texture(tex2n, detail_uv)*mask1.b;
        norm_map+=texture(tex3n, detail_uv)*mask2.r;
        norm_map+=texture(tex4n, detail_uv)*mask2.g;
        norm_map+=texture(tex5n, detail_uv)*mask2.b;        
    gloss=clamp(norm_map.a*5.0, 0.0, 1.0); //the gloss factor in the default textures suck, needs to be boosted!
    norm_map=norm_map*2.0-1.0;
    vec3 T=  cross(N, Left);  
    vec3 B= cross(N, T); 
    N.xyz *= norm_map.z;
    N.xyz += T * norm_map.x;
    N.xyz += B * norm_map.y;    
    //norm+=normal;
    N = normalize(N);
    
    //lights...    
    //...directional
    color+=light_vec_color*max(dot(N,-light_vec), 0.0);        
    specular +=pow(max(dot(reflect(-light_vec,N), V), 0.0), 6.0+gloss*4.0)*gloss;
    //..point
    vec3 L;
    vec3 R;
    float att;   
    float ldist;
    for (int i=0; i<num_lights; ++i)
        { 
        //diffuse
        L = normalize(light_pos[i].xyz-world_pos.xyz);
        ldist=distance(world_pos.xyz, light_pos[i].xyz);
        att = 1/(light_att[i].x + light_att[i].y*ldist + light_att[i].z*ldist*ldist);        
        color+=light_color[i].rgb*max(dot(N,L), 0.0)*att;
        //specular
        R=reflect(L,N)*att;
        specular +=pow(max(dot(R, V), 0.0), 6.0+gloss*4.0)*gloss*light_color[i].a;    
        }
    
    //...spot
    //no spotlights!
    
    //add spec to dif
    color+=specular;
    
    //shadows
    color*= textureProj(shadow_caster.shadowMap,shadow_uv, 0.1)*0.5;  
    //color*=PCF(shadow_caster.shadowMap,shadow_uv, 0.1);  
    
    //...ambient 
    color+= ambient; 
    
    //fog
    //float fog_factor=distance(world_pos.xyz,camera_pos)*0.015;      
    //fog_factor=clamp(fog_factor-0.1, 0.0, 0.6); 
    //vec3 fog_color=vec3(0.6, 0.6, 0.65);    
    //final color with fog   
    //final_color=vec4(mix(color*detail, fog_color, fog_factor), 1.0);
    
    //final color
    final_color=vec4(color*detail, 1.0);
    }
