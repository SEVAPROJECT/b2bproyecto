-- Trigger function corregida para manejar nuevos usuarios de Supabase Auth
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER AS $trigger$
DECLARE
    user_metadata JSONB;
    user_ruc TEXT;
    user_nombre TEXT;
    user_empresa TEXT;
BEGIN
    -- Obtener metadata del usuario de Supabase Auth
    user_metadata := NEW.raw_user_meta_data;
    
    -- Extraer datos de la metadata
    user_nombre := COALESCE(user_metadata->>'nombre_persona', 'Usuario');
    user_empresa := user_metadata->>'nombre_empresa';
    user_ruc := user_metadata->>'ruc';
    
    -- Log para debugging
    RAISE NOTICE 'Creando perfil para usuario: %, Nombre: %, Empresa: %, RUC: %', 
        NEW.id, user_nombre, user_empresa, user_ruc;
    
    -- Insertar en la tabla public.users con estado ACTIVO
    INSERT INTO public.users (
        id,
        nombre_persona,
        nombre_empresa,
        ruc,
        estado
    ) VALUES (
        NEW.id,
        user_nombre,
        user_empresa,
        user_ruc,
        'ACTIVO'
    );
    
    RAISE NOTICE 'Perfil creado exitosamente para usuario: %', NEW.id;
    
    -- Obtener el ID del rol "Cliente" y asignarlo
    INSERT INTO public.usuario_rol (id_usuario, id_rol)
    SELECT NEW.id, id FROM public.rol WHERE nombre = 'Cliente';
    
    RETURN NEW;
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Error creando perfil de usuario: %', SQLERRM;
        RETURN NEW;
END;
$trigger$ LANGUAGE plpgsql SECURITY DEFINER;

-- Crear el trigger si no existe
DROP TRIGGER IF EXISTS on_auth_user_created_trigger ON auth.users;
CREATE TRIGGER on_auth_user_created_trigger
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user();


