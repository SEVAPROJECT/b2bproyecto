-- ============================================================
-- Migración: Actualizar trigger para crear usuarios con estado INACTIVO
-- ============================================================
-- Este script actualiza la función handle_new_auth_user para que
-- cree usuarios con estado 'INACTIVO' en lugar de 'ACTIVO'
-- según el nuevo flujo de verificación de RUC
-- ============================================================

-- Actualizar la función handle_new_auth_user
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()  
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
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

    -- Insertar en la tabla public.users con estado INACTIVO (cambiar de 'ACTIVO' a 'INACTIVO')
    -- El usuario quedará INACTIVO hasta que se apruebe el RUC
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
        'INACTIVO'  -- Cambiado de 'ACTIVO' a 'INACTIVO'
    );

    RAISE NOTICE 'Perfil creado exitosamente para usuario: % con estado INACTIVO', NEW.id;

    -- Obtener el ID del rol "Cliente" y asignarlo        
    INSERT INTO public.usuario_rol (id_usuario, id_rol)   
    SELECT NEW.id, id FROM public.rol WHERE nombre = 'Cliente';

    RETURN NEW;
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Error creando perfil de usuario: %', SQLERRM;
        RETURN NEW;
END;
$function$;

-- Comentario explicativo
COMMENT ON FUNCTION public.handle_new_auth_user() IS 
'Crea el perfil de usuario en public.users cuando se crea un usuario en Supabase Auth. 
Crea el usuario con estado INACTIVO hasta que se apruebe el RUC.';

