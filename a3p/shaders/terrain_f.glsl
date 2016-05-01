#version 150

uniform vec4 light_color[100];
uniform vec4 light_pos[100];
uniform vec4 light_att[100];
uniform int num_lights;
uniform vec3 camera_pos;
uniform vec3 ambient;
uniform vec3 light_vec;
uniform vec3 light_vec_color;
uniform sampler2D height_map;

in vec2 terrain_uv;
in vec4 world_pos;

out vec4 final_color;

void main()
    {
    vec3 N=normalize(texture(height_map,terrain_uv).xyz*2.0-1.0);
    vec3 V = normalize(world_pos.xyz - camera_pos); 
    vec3 color=vec3(0.0, 0.0, 0.0);
    float specular =0.0; 
    //ambient 
    color+= ambient; 
    //directional
    color+=light_vec_color*max(dot(N,-light_vec), 0.0);
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
        specular +=pow(max(dot(R, V), 0.0), 10.0)*light_color[i].a;
        }
    
    final_color=vec4(color+specular, 1.0);  
    //final_color=vec4(N, 1.0);  
    }
